
"""
controller.py
============================================================
FLUXXWAVE EV PROJECT — SUPERVISORY CONTROLLER

PURPOSE
-------
Coordinate the simulation modules and maintain a central view
of the simulated vehicle's operating state.

RESPONSIBILITIES
----------------
1. Initialize the supervisory controller.
2. Check the availability of required simulation components.
3. Read battery, energy, and controller state.
4. Validate simulation inputs.
5. Evaluate operating conditions and battery availability.
6. Execute a simulation step when inputs are valid.
7. Detect and record simulated faults and warnings.
8. Maintain a central system status.
9. Export event records to CSV.

DEPENDENCIES
------------
battery.py
battery_manager.py
energy_simulator.py

The energy simulator remains responsible for energy calculations.
The battery manager remains responsible for battery selection.
This module coordinates them rather than duplicating their logic.

SAFETY
------
This is a software simulation controller only.
It must not directly control a real traction battery, motor,
contactor, charging circuit, or other vehicle hardware.
============================================================
"""

from datetime import datetime
from pathlib import Path
import csv
import math


# ============================================================
# 1. IMPORT THE SIMULATION MODULE
# ============================================================

# Import the main simulation functions.
#
# If a required module is missing, the controller can still be
# imported, but it will report that the simulator is unavailable.
try:
    from energy_simulator import (
        initialize_simulation,
        run_simulation_step,
        calculate_summary,
    )

    SIMULATOR_AVAILABLE = True
    SIMULATOR_IMPORT_ERROR = None

except ImportError as error:
    initialize_simulation = None
    run_simulation_step = None
    calculate_summary = None

    SIMULATOR_AVAILABLE = False
    SIMULATOR_IMPORT_ERROR = str(error)


# ============================================================
# 2. DEFAULT CONTROLLER CONFIGURATION
# ============================================================

DEFAULT_CONTROLLER_CONFIG = {
    # A simulated solar irradiance above this value is rejected.
    # This is an input-validation limit, not a weather forecast.
    "maximum_irradiance_w_m2": 1500.0,

    # Maximum accepted simulated vehicle speed.
    "maximum_speed_mps": 100.0,

    # Warn if the energy-balance error exceeds this tolerance.
    "balance_warning_tolerance_kwh": 1e-6,

    # A simulation step cannot execute without a usable simulator.
    "require_simulator": True,

    # Continue simulation when a noncritical warning is present.
    "allow_warnings": True,

    # Whether to record routine successful control steps.
    "log_successful_steps": False,
}


# ============================================================
# 3. INPUT VALIDATION
# ============================================================

def validate_numeric_input(value, name):
    """
    Convert an input to a finite float.

    Reject strings that cannot be converted, NaN, and infinity.
    """

    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{name} must be a valid number."
        )

    if not math.isfinite(number):
        raise ValueError(
            f"{name} must be finite."
        )

    return number


def validate_non_negative_input(value, name):
    """Validate a finite number that cannot be negative."""

    number = validate_numeric_input(value, name)

    if number < 0.0:
        raise ValueError(
            f"{name} cannot be negative."
        )

    return number


def validate_boolean_input(value, name):
    """
    Require an actual Boolean for flags such as braking.

    This avoids silently treating arbitrary strings or integers
    as valid operating commands.
    """

    if not isinstance(value, bool):
        raise ValueError(
            f"{name} must be True or False."
        )

    return value


# ============================================================
# 4. CENTRAL EVENT LOGGER
# ============================================================

def record_event(
    controller,
    event_type,
    message,
    severity="INFO",
    details=None,
):
    """
    Add an event to the controller's central event history.

    Parameters
    ----------
    controller:
        Controller state dictionary.

    event_type:
        Short machine-readable event name.

    message:
        Human-readable explanation.

    severity:
        INFO, WARNING, or ERROR.

    details:
        Optional additional information.
    """

    event = {
        "timestamp": datetime.now().isoformat(
            timespec="seconds"
        ),
        "event_type": str(event_type),
        "severity": str(severity).upper(),
        "message": str(message),
        "details": repr(details) if details is not None else "",
    }

    controller["events"].append(event)

    # Keep the central status synchronized with serious events.
    if event["severity"] == "ERROR":
        controller["last_error"] = event["message"]

    return event


# ============================================================
# 5. INITIALIZE THE CONTROLLER
# ============================================================

def initialize_controller(config=None):
    """
    Initialize the supervisory controller and energy simulation.

    Parameters
    ----------
    config:
        Optional dictionary containing controller settings and
        simulation settings.

        Controller settings:
            maximum_irradiance_w_m2
            maximum_speed_mps
            balance_warning_tolerance_kwh
            require_simulator
            allow_warnings
            log_successful_steps

        Any other configuration keys are passed to
        energy_simulator.initialize_simulation().

    Returns
    -------
    dict
        The complete controller state.

    Example
    -------
    controller = initialize_controller({
        "step_seconds": 60,
        "duration_seconds": 3600,
    })
    """

    # Start with default supervisory settings.
    settings = dict(DEFAULT_CONTROLLER_CONFIG)

    if config is not None:
        settings.update(config)

    # Validate controller-specific limits.
    settings["maximum_irradiance_w_m2"] = (
        validate_numeric_input(
            settings["maximum_irradiance_w_m2"],
            "maximum_irradiance_w_m2",
        )
    )

    settings["maximum_speed_mps"] = (
        validate_numeric_input(
            settings["maximum_speed_mps"],
            "maximum_speed_mps",
        )
    )

    settings["balance_warning_tolerance_kwh"] = (
        validate_non_negative_input(
            settings["balance_warning_tolerance_kwh"],
            "balance_warning_tolerance_kwh",
        )
    )

    if settings["maximum_irradiance_w_m2"] <= 0:
        raise ValueError(
            "Maximum irradiance must be greater than zero."
        )

    if settings["maximum_speed_mps"] <= 0:
        raise ValueError(
            "Maximum speed must be greater than zero."
        )

    if not isinstance(settings["require_simulator"], bool):
        raise ValueError(
            "require_simulator must be True or False."
        )

    if not isinstance(settings["allow_warnings"], bool):
        raise ValueError(
            "allow_warnings must be True or False."
        )

    # Track whether each required component is available.
    component_status = {
        "energy_simulator": SIMULATOR_AVAILABLE,
        "battery_module": False,
        "battery_manager_module": False,
    }

    # Check the battery-related imports independently.
    try:
        import battery
        component_status["battery_module"] = True
    except ImportError:
        pass

    try:
        import battery_manager
        component_status["battery_manager_module"] = True
    except ImportError:
        pass

    # Create the central controller state before initialization
    # so initialization failures can still be recorded.
    controller = {
        "config": settings,
        "simulation": None,
        "component_status": component_status,

        # Overall states include INITIALIZING, READY, RUNNING,
        # WARNING, ERROR, and SIMULATOR_UNAVAILABLE.
        "system_status": "INITIALIZING",
        "status_message": "Controller initialization started.",

        "warnings": [],
        "events": [],
        "last_error": None,

        # Counts of successful and rejected simulation steps.
        "successful_steps": 0,
        "rejected_steps": 0,

        # Most recent validated input values.
        "last_inputs": None,

        # Most recent result from energy_simulator.py.
        "last_step_result": None,

        # Timestamp of controller initialization.
        "initialized_at": datetime.now().isoformat(
            timespec="seconds"
        ),
    }

    record_event(
        controller,
        "INITIALIZATION_STARTED",
        "Supervisory controller initialization started.",
    )

    # If the simulator is required but unavailable, stop here.
    if (
        settings["require_simulator"]
        and not SIMULATOR_AVAILABLE
    ):

        controller["system_status"] = (
            "SIMULATOR_UNAVAILABLE"
        )

        controller["status_message"] = (
            "The energy simulator could not be imported."
        )

        record_event(
            controller,
            "SIMULATOR_IMPORT_FAILED",
            controller["status_message"],
            severity="ERROR",
            details=SIMULATOR_IMPORT_ERROR,
        )

        return controller

    # A controller without the simulator cannot execute energy
    # simulation steps, even if initialization was requested.
    if not SIMULATOR_AVAILABLE:

        controller["system_status"] = (
            "SIMULATOR_UNAVAILABLE"
        )

        controller["status_message"] = (
            "Controller initialized without an energy simulator."
        )

        record_event(
            controller,
            "SIMULATOR_UNAVAILABLE",
            controller["status_message"],
            severity="WARNING",
            details=SIMULATOR_IMPORT_ERROR,
        )

        return controller

    try:
        # Remove controller-only settings before passing the
        # remaining settings to the energy simulator.
        controller_only_keys = set(
            DEFAULT_CONTROLLER_CONFIG.keys()
        )

        simulation_config = {
            key: value
            for key, value in settings.items()
            if key not in controller_only_keys
        }

        simulation = initialize_simulation(
            simulation_config
        )

        controller["simulation"] = simulation

        controller["system_status"] = "READY"

        controller["status_message"] = (
            "Controller and energy simulation initialized."
        )

        record_event(
            controller,
            "INITIALIZATION_SUCCESS",
            controller["status_message"],
        )

        # Report unavailable battery components.
        read_system_state(controller)

    except Exception as error:

        controller["system_status"] = "ERROR"

        controller["status_message"] = (
            f"Initialization failed: {error}"
        )

        record_event(
            controller,
            "INITIALIZATION_FAILED",
            controller["status_message"],
            severity="ERROR",
        )

    return controller


# ============================================================
# 6. READ THE CURRENT SYSTEM STATE
# ============================================================

def read_system_state(controller):
    """
    Read the latest state of the simulation.

    This function observes state; it does not change battery SoC
    or run a new energy simulation step.

    Returns
    -------
    dict
        A snapshot of component availability, battery state,
        simulation time, and controller status.
    """

    simulation = controller.get("simulation")

    # A failed initialization may leave no simulation state.
    if simulation is None:

        snapshot = {
            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            ),
            "system_status": controller["system_status"],
            "status_message": controller["status_message"],
            "component_status": dict(
                controller["component_status"]
            ),
            "simulation_available": False,
            "battery_manager": None,
            "batteries": {},
            "simulation_time_seconds": None,
        }

        controller["last_system_state"] = snapshot

        return snapshot

    batteries = simulation["batteries"]
    manager = simulation["battery_manager"]

    # Obtain the manager's own state report.
    manager_state = manager.get_controller_state()

    # Collect a compact status for each battery.
    battery_states = {}

    for battery_id, battery in batteries.items():

        battery_states[battery_id] = {
            "soc_percent": battery.soc_percent,
            "stored_energy_kwh": battery.stored_energy_kwh,
            "available_energy_kwh": (
                battery.available_energy_kwh
            ),
            "enabled": getattr(
                battery, "enabled", False
            ),
            "faults": list(
                getattr(battery, "faults", [])
            ),
            "eligible": manager._battery_is_eligible(
                battery_id
            ),
        }

    # The solar model is part of the simulator, so it is
    # considered available when the simulator imports correctly.
    component_status = dict(
        controller["component_status"]
    )

    component_status["battery_a_eligible"] = (
        battery_states["A"]["eligible"]
    )

    component_status["battery_b_eligible"] = (
        battery_states["B"]["eligible"]
    )

    snapshot = {
        "timestamp": datetime.now().isoformat(
            timespec="seconds"
        ),
        "system_status": controller["system_status"],
        "status_message": controller["status_message"],
        "component_status": component_status,
        "simulation_available": True,
        "simulation_time_seconds": simulation["time_seconds"],
        "active_battery_id": manager.active_battery_id,
        "battery_manager": manager_state,
        "batteries": battery_states,
        "successful_steps": controller["successful_steps"],
        "rejected_steps": controller["rejected_steps"],
    }

    controller["last_system_state"] = snapshot

    return snapshot


# ============================================================
# 7. EVALUATE OPERATING CONDITIONS
# ============================================================

def evaluate_operating_conditions(
    controller,
    speed_mps,
    irradiance_w_m2,
    braking=False,
):
    """
    Validate inputs and evaluate whether a step may execute.

    Checks include:
    - Required simulator availability.
    - Numeric input validity.
    - Speed and irradiance limits.
    - Boolean braking flag.
    - Battery availability.
    - Existing battery faults.

    Returns
    -------
    dict
        {
            "allowed": bool,
            "errors": list,
            "warnings": list,
            "validated_inputs": dict or None
        }

    A rejected step does not call the energy simulator.
    """

    errors = []
    warnings = []
    validated_inputs = None

    # --------------------------------------------------------
    # A. Check whether the simulation exists.
    # --------------------------------------------------------

    if controller.get("simulation") is None:

        errors.append(
            "Energy simulation is not initialized."
        )

    if not SIMULATOR_AVAILABLE:

        errors.append(
            "Required energy simulator is unavailable."
        )

    # --------------------------------------------------------
    # B. Validate the input values.
    # --------------------------------------------------------

    try:
        speed = validate_non_negative_input(
            speed_mps,
            "speed_mps",
        )

        irradiance = validate_non_negative_input(
            irradiance_w_m2,
            "irradiance_w_m2",
        )

        braking_value = validate_boolean_input(
            braking,
            "braking",
        )

        if speed > controller["config"][
            "maximum_speed_mps"
        ]:

            errors.append(
                "Vehicle speed exceeds the configured limit."
            )

        if irradiance > controller["config"][
            "maximum_irradiance_w_m2"
        ]:

            errors.append(
                "Solar irradiance exceeds the configured limit."
            )

        validated_inputs = {
            "speed_mps": speed,
            "irradiance_w_m2": irradiance,
            "braking": braking_value,
        }

    except ValueError as error:

        errors.append(str(error))

    # --------------------------------------------------------
    # C. Check the simulated battery system.
    # --------------------------------------------------------

    simulation = controller.get("simulation")

    if simulation is not None:

        manager = simulation["battery_manager"]

        batteries = simulation["batteries"]

        eligible_batteries = [
            battery_id
            for battery_id, battery in batteries.items()
            if manager._battery_is_eligible(battery_id)
        ]

        if not eligible_batteries:

            warnings.append(
                "Neither battery is currently eligible."
            )

        elif manager.active_battery_id is None:

            warnings.append(
                "No active battery is selected."
            )

        # Battery faults are warnings unless they cause the
        # input or system configuration itself to be invalid.
        for battery_id, battery in batteries.items():

            faults = getattr(battery, "faults", [])

            if faults:

                warnings.append(
                    f"Battery {battery_id} has recorded faults: "
                    f"{faults}"
                )

    # --------------------------------------------------------
    # D. Update the controller's warning list.
    # --------------------------------------------------------

    controller["warnings"] = list(warnings)

    for warning in warnings:

        record_event(
            controller,
            "OPERATING_WARNING",
            warning,
            severity="WARNING",
        )

    # Record rejected inputs without executing a step.
    if errors:

        for error_message in errors:

            record_event(
                controller,
                "INPUT_OR_CONDITION_REJECTED",
                error_message,
                severity="ERROR",
                details={
                    "speed_mps": repr(speed_mps),
                    "irradiance_w_m2": repr(irradiance_w_m2),
                    "braking": repr(braking),
                },
            )

        controller["rejected_steps"] += 1

        controller["system_status"] = "ERROR"

        controller["status_message"] = (
            "Control step rejected: " + "; ".join(errors)
        )

    elif warnings:

        controller["system_status"] = "WARNING"

        controller["status_message"] = (
            "Operating conditions contain warnings."
        )

    else:

        controller["system_status"] = "READY"

        controller["status_message"] = (
            "Operating conditions are valid."
        )

    # Warnings may be configured to prevent execution.
    allowed = (
        not errors
        and (
            controller["config"]["allow_warnings"]
            or not warnings
        )
    )

    return {
        "allowed": allowed,
        "errors": errors,
        "warnings": warnings,
        "validated_inputs": validated_inputs,
    }


# ============================================================
# 8. EXECUTE ONE SUPERVISORY CONTROL STEP
# ============================================================

def execute_control_step(
    controller,
    speed_mps,
    irradiance_w_m2,
    braking=False,
):
    """
    Validate conditions and execute one simulation step.

    Sequence
    --------
    1. Evaluate operating conditions.
    2. Reject invalid inputs.
    3. Run one step of the energy simulation.
    4. Inspect the energy balance.
    5. Record the result and update system status.

    Returns
    -------
    dict
        A combined controller and simulation result.
    """

    # --------------------------------------------------------
    # A. Evaluate operating conditions.
    # --------------------------------------------------------

    evaluation = evaluate_operating_conditions(
        controller=controller,
        speed_mps=speed_mps,
        irradiance_w_m2=irradiance_w_m2,
        braking=braking,
    )

    # Do not execute a simulation step if the conditions fail.
    if not evaluation["allowed"]:

        result = {
            "success": False,
            "system_status": controller["system_status"],
            "status_message": controller["status_message"],
            "evaluation": evaluation,
            "simulation_result": None,
        }

        controller["last_step_result"] = result

        return result

    # --------------------------------------------------------
    # B. Retrieve validated values.
    # --------------------------------------------------------

    inputs = evaluation["validated_inputs"]

    controller["last_inputs"] = dict(inputs)

    simulation = controller["simulation"]

    # --------------------------------------------------------
    # C. Run the simulation step.
    # --------------------------------------------------------

    controller["system_status"] = "RUNNING"

    controller["status_message"] = (
        "Simulation step is executing."
    )

    try:

        step_result = run_simulation_step(
            state=simulation,
            speed_mps=inputs["speed_mps"],
            irradiance_w_m2=inputs["irradiance_w_m2"],
            braking=inputs["braking"],
        )

        controller["successful_steps"] += 1

        controller["last_step_result"] = step_result

        # ----------------------------------------------------
        # D. Inspect the energy balance.
        # ----------------------------------------------------

        balance_error = abs(
            step_result["energy"]["balance_error_kwh"]
        )

        tolerance = controller["config"][
            "balance_warning_tolerance_kwh"
        ]

        if balance_error > tolerance:

            warning = (
                "Energy-balance error exceeded the configured "
                f"tolerance: {balance_error:.12g} kWh."
            )

            controller["warnings"].append(warning)

            record_event(
                controller,
                "ENERGY_BALANCE_WARNING",
                warning,
                severity="WARNING",
                details={
                    "balance_error_kwh": balance_error,
                    "tolerance_kwh": tolerance,
                },
            )

            controller["system_status"] = "WARNING"

            controller["status_message"] = warning

        else:

            controller["system_status"] = "READY"

            controller["status_message"] = (
                "Simulation step completed successfully."
            )

        # ----------------------------------------------------
        # E. Record the successful step when configured.
        # ----------------------------------------------------

        if controller["config"]["log_successful_steps"]:

            record_event(
                controller,
                "CONTROL_STEP_SUCCESS",
                "Simulation step completed.",
                details={
                    "time_seconds": (
                        step_result["time_seconds"]
                    ),
                    "balance_error_kwh": (
                        step_result["energy"][
                            "balance_error_kwh"
                        ]
                    ),
                },
            )

        # A fresh snapshot makes the latest state easy to inspect.
        snapshot = read_system_state(controller)

        result = {
            "success": True,
            "system_status": controller["system_status"],
            "status_message": controller["status_message"],
            "evaluation": evaluation,
            "simulation_result": step_result,
            "system_state": snapshot,
        }

        controller["last_step_result"] = result

        return result

    except Exception as error:

        # Unexpected simulation errors are recorded centrally.
        controller["system_status"] = "ERROR"

        controller["status_message"] = (
            f"Simulation step failed: {error}"
        )

        controller["last_error"] = str(error)

        record_event(
            controller,
            "SIMULATION_STEP_FAILED",
            controller["status_message"],
            severity="ERROR",
        )

        result = {
            "success": False,
            "system_status": controller["system_status"],
            "status_message": controller["status_message"],
            "evaluation": evaluation,
            "simulation_result": None,
        }

        controller["last_step_result"] = result

        return result


# ============================================================
# 9. GET THE CENTRAL SYSTEM STATUS
# ============================================================

def get_system_status(controller):
    """
    Return a concise central status report.

    The status includes:
    - Overall system status.
    - Component availability.
    - Active battery.
    - Battery SoC.
    - Simulation time.
    - Warnings and errors.
    - Step counters.
    """

    snapshot = read_system_state(controller)

    simulation = controller.get("simulation")

    active_battery_id = None

    battery_soc = {}

    if simulation is not None:

        manager = simulation["battery_manager"]

        active_battery_id = manager.active_battery_id

        for battery_id, battery in (
            simulation["batteries"].items()
        ):

            battery_soc[battery_id] = (
                battery.soc_percent
            )

    return {
        "timestamp": datetime.now().isoformat(
            timespec="seconds"
        ),
        "system_status": controller["system_status"],
        "status_message": controller["status_message"],
        "component_status": dict(
            controller["component_status"]
        ),
        "simulation_available": (
            simulation is not None
        ),
        "simulation_time_seconds": (
            snapshot["simulation_time_seconds"]
        ),
        "active_battery_id": active_battery_id,
        "battery_soc_percent": battery_soc,
        "warning_count": len(controller["warnings"]),
        "event_count": len(controller["events"]),
        "successful_steps": controller["successful_steps"],
        "rejected_steps": controller["rejected_steps"],
        "last_error": controller["last_error"],
    }


# ============================================================
# 10. PRINT A CENTRAL STATUS REPORT
# ============================================================

def print_system_status(controller):
    """Print a human-readable supervisory status report."""

    status = get_system_status(controller)

    print("\n" + "=" * 64)
    print("FLUXXWAVE — SUPERVISORY CONTROLLER")
    print("=" * 64)

    print(
        f"System status       : {status['system_status']}"
    )

    print(
        f"Status message      : {status['status_message']}"
    )

    print(
        f"Simulation available: {status['simulation_available']}"
    )

    print(
        f"Simulation time     : "
        f"{status['simulation_time_seconds']}"
    )

    print(
        f"Active battery      : "
        f"{status['active_battery_id'] or 'NONE'}"
    )

    print("\nBATTERY SoC")

    if status["battery_soc_percent"]:

        for battery_id, soc in (
            status["battery_soc_percent"].items()
        ):

            print(
                f"  Battery {battery_id}: {soc:.2f}%"
            )

    else:

        print("  No battery state available.")

    print("\nCOMPONENT AVAILABILITY")

    for component, available in (
        status["component_status"].items()
    ):

        print(
            f"  {component}: {available}"
        )

    print("\nEVENT COUNTS")

    print(
        f"  Warnings           : {status['warning_count']}"
    )

    print(
        f"  Events             : {status['event_count']}"
    )

    print(
        f"  Successful steps   : {status['successful_steps']}"
    )

    print(
        f"  Rejected steps     : {status['rejected_steps']}"
    )

    if status["last_error"]:

        print(
            f"\nLast error: {status['last_error']}"
        )

    print("=" * 64)


# ============================================================
# 11. EXPORT CONTROLLER EVENTS TO CSV
# ============================================================

def export_controller_events(
    controller,
    filename="data/controller_events.csv",
):
    """
    Export warnings, initialization events, errors, and
    optional successful-step events to CSV.
    """

    output_path = Path(filename)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "timestamp",
        "event_type",
        "severity",
        "message",
        "details",
    ]

    with output_path.open(
        mode="w",
        newline="",
        encoding="utf-8",
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        writer.writerows(
            controller["events"]
        )

    print(
        f"Controller events exported to: {output_path}"
    )

    return str(output_path)


# ============================================================
# 12. RUN A SHORT DEMONSTRATION
# ============================================================

def main():
    """
    Demonstrate controller initialization, normal operation,
    invalid-input rejection, status reporting, and event export.
    """

    print("Initializing Fluxxwave supervisory controller...")

    controller = initialize_controller({
        # Settings passed through to energy_simulator.py.
        "step_seconds": 60.0,
        "duration_seconds": 3600.0,

        # Supervisory limits.
        "maximum_speed_mps": 100.0,
        "maximum_irradiance_w_m2": 1500.0,

        # Log successful control steps for this demo.
        "log_successful_steps": True,
    })

    print_system_status(controller)

    # Stop the demonstration if initialization failed.
    if controller["simulation"] is None:

        print(
            "\nSimulation could not start. Check that "
            "battery.py, battery_manager.py, and "
            "energy_simulator.py are in the same folder."
        )

        export_controller_events(controller)

        return

    # --------------------------------------------------------
    # DEMO 1: A valid operating step.
    # --------------------------------------------------------

    print("\nDEMO 1: VALID CONTROL STEP")

    result = execute_control_step(
        controller=controller,
        speed_mps=8.0,
        irradiance_w_m2=500.0,
        braking=False,
    )

    print("Success:", result["success"])
    print("Status:", result["system_status"])

    # --------------------------------------------------------
    # DEMO 2: A simulated braking step.
    # --------------------------------------------------------

    print("\nDEMO 2: BRAKING STEP")

    result = execute_control_step(
        controller=controller,
        speed_mps=4.0,
        irradiance_w_m2=300.0,
        braking=True,
    )

    print("Success:", result["success"])
    print("Status:", result["system_status"])

    # --------------------------------------------------------
    # DEMO 3: Reject an invalid input.
    # --------------------------------------------------------

    print("\nDEMO 3: INVALID INPUT")

    result = execute_control_step(
        controller=controller,
        speed_mps=-5.0,
        irradiance_w_m2=300.0,
        braking=False,
    )

    print("Success:", result["success"])
    print("Status:", result["system_status"])
    print("Message:", result["status_message"])

    # --------------------------------------------------------
    # DEMO 4: Final status and event export.
    # --------------------------------------------------------

    print("\nFINAL SYSTEM STATUS")

    print_system_status(controller)

    export_controller_events(controller)

    print("\nController demonstration completed.")


# ============================================================
# 13. SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
