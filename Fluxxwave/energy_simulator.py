
"""
energy_simulator.py
============================================================
FLUXXWAVE EV PROJECT — MAIN ENERGY SIMULATION

PURPOSE
-------
Integrates the solar, regenerative braking, battery, and
dual-battery management models into one simulation.

MAIN RESPONSIBILITIES
---------------------
1. Calculate vehicle electrical demand.
2. Calculate solar electrical energy available.
3. Estimate regenerative energy during braking.
4. Supply vehicle demand from available energy sources.
5. Charge and discharge the simulated batteries.
6. Track conversion losses and unused/curtailed energy.
7. Maintain an explicit energy balance at every time step.
8. Store energy, battery, and power histories.
9. Compare scenarios with different configurations.
10. Export results to CSV.

ENERGY ACCOUNTING CONVENTION
----------------------------
All energy quantities used in the energy balance are in kWh.

Solar input:
    Electrical energy available from the solar model.

Regenerative input:
    Electrical energy recovered during a simulated braking event.

Vehicle demand:
    Electrical energy requested by the vehicle at the DC bus.

Battery discharge:
    Energy removed from the battery's stored energy.

Battery charge:
    Energy delivered to the battery input, with only the
    efficiency-adjusted portion added to stored energy.

Conversion losses:
    Energy lost during battery charging and discharging.

Curtailed energy:
    Available solar or regenerative energy that cannot be
    used or stored in the current time step.

IMPORTANT
---------
This is a simplified software model. It is not suitable for
direct control of a real traction battery or vehicle.
============================================================
"""

from datetime import datetime
from os import stat_result
from pathlib import Path
import csv
import math

from battery import create_battery_a, create_battery_b
from battery_manager import BatteryManager


# ============================================================
# 1. DEFAULT SIMULATION CONFIGURATION
# ============================================================

DEFAULT_CONFIG = {
    # Duration of one simulation step, in seconds.
    "step_seconds": 60.0,

    # Total simulation duration, in seconds.
    "duration_seconds": 3600.0,

    # Vehicle properties.
    "vehicle_mass_kg": 1200.0,
    "drag_coefficient": 0.29,
    "frontal_area_m2": 2.2,
    "air_density_kg_m3": 1.225,
    "rolling_resistance_coefficient": 0.012,

    # Simplified drivetrain efficiency.
    "drivetrain_efficiency": 0.90,

    # Electrical auxiliary demand, such as lights and electronics.
    "auxiliary_power_w": 300.0,

    # Regenerative braking efficiency.
    "regenerative_efficiency": 0.70,

    # Fraction of kinetic-energy reduction available to the
    # simplified regenerative model after unmodelled effects.
    #
    # This is an additional modelling assumption, not a measured
    # property of a real vehicle.
    "braking_energy_availability_factor": 0.80,

    # Maximum fraction of the vehicle's mass-related kinetic
    # energy reduction considered in a braking event.
    #
    # The model still does not represent a real motor map,
    # braking controller, road gradient, or tire behavior.
    "switch_threshold_percent": 20.0,
    "hysteresis_percent": 5.0,

    # Default solar model configuration.
    "solar_panel_area_m2": 2.0,
    "solar_panel_efficiency": 0.22,
    "solar_system_efficiency": 0.95,
    "solar_shading_fraction": 0.0,

    # Default battery charging efficiency.
    "battery_charge_efficiency": 0.95,

    # The following settings can be overridden in a scenario.
    "initial_speed_mps": 0.0,
}


# ============================================================
# 2. VALIDATION HELPERS
# ============================================================

def require_finite_number(value, name):
    """Convert a value to float and reject NaN or infinity."""

    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number.")

    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")

    return value


def require_non_negative(value, name):
    """Validate a quantity that cannot be negative."""

    value = require_finite_number(value, name)

    if value < 0:
        raise ValueError(f"{name} cannot be negative.")

    return value


def require_positive(value, name):
    """Validate a quantity that must be greater than zero."""

    value = require_finite_number(value, name)

    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")

    return value


def require_fraction(value, name):
    """Validate a fraction between zero and one."""

    value = require_finite_number(value, name)

    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1.")

    return value


# ============================================================
# 3. VEHICLE ELECTRICAL LOAD MODEL
# ============================================================

def calculate_load(
    speed_mps,
    vehicle_mass_kg=1200.0,
    drag_coefficient=0.29,
    frontal_area_m2=2.2,
    air_density_kg_m3=1.225,
    rolling_resistance_coefficient=0.012,
    drivetrain_efficiency=0.90,
    auxiliary_power_w=300.0,
):
    """
    Estimate vehicle electrical demand.

    Parameters
    ----------
    speed_mps:
        Vehicle speed in metres per second.

    vehicle_mass_kg:
        Vehicle mass in kilograms.

    drag_coefficient:
        Simplified aerodynamic drag coefficient.

    frontal_area_m2:
        Vehicle frontal area in square metres.

    air_density_kg_m3:
        Air density in kilograms per cubic metre.

    rolling_resistance_coefficient:
        Simplified tire/road rolling resistance coefficient.

    drivetrain_efficiency:
        Fraction of electrical traction power converted into
        useful mechanical power.

    auxiliary_power_w:
        Electrical demand of auxiliary equipment.

    Returns
    -------
    dict
        Power components and total DC-bus electrical demand.

    MODEL LIMITATIONS
    -----------------
    This model assumes level ground and steady speed during
    each step. It excludes acceleration demand, road gradient,
    wind, detailed motor efficiency maps, and tire dynamics.

    Acceleration and braking effects must be represented
    separately by the simulation's speed profile.
    """

    speed_mps = require_non_negative(speed_mps, "speed_mps")
    vehicle_mass_kg = require_positive(
        vehicle_mass_kg, "vehicle_mass_kg"
    )
    drag_coefficient = require_non_negative(
        drag_coefficient, "drag_coefficient"
    )
    frontal_area_m2 = require_non_negative(
        frontal_area_m2, "frontal_area_m2"
    )
    air_density_kg_m3 = require_positive(
        air_density_kg_m3, "air_density_kg_m3"
    )
    rolling_resistance_coefficient = require_non_negative(
        rolling_resistance_coefficient,
        "rolling_resistance_coefficient",
    )
    drivetrain_efficiency = require_fraction(
        drivetrain_efficiency, "drivetrain_efficiency"
    )
    auxiliary_power_w = require_non_negative(
        auxiliary_power_w, "auxiliary_power_w"
    )

    if drivetrain_efficiency == 0:
        raise ValueError(
            "drivetrain_efficiency must be greater than zero."
        )

    gravity_mps2 = 9.81

    # Rolling resistance force, approximately constant at a
    # given mass on level ground.
    rolling_force_n = (
        rolling_resistance_coefficient
        * vehicle_mass_kg
        * gravity_mps2
    )

    # Aerodynamic drag force increases with the square of speed.
    aerodynamic_force_n = (
        0.5
        * air_density_kg_m3
        * drag_coefficient
        * frontal_area_m2
        * speed_mps ** 2
    )

    # Mechanical power is force multiplied by speed.
    rolling_power_w = rolling_force_n * speed_mps

    aerodynamic_power_w = (
        aerodynamic_force_n * speed_mps
    )

    # Convert useful mechanical traction power into an
    # estimate of required electrical traction power.
    mechanical_traction_power_w = (
        rolling_power_w + aerodynamic_power_w
    )

    traction_electrical_power_w = (
        mechanical_traction_power_w
        / drivetrain_efficiency
    )

    # Auxiliary loads are already electrical power demands.
    total_demand_w = (
        traction_electrical_power_w
        + auxiliary_power_w
    )

    return {
        "speed_mps": speed_mps,
        "speed_kmh": speed_mps * 3.6,
        "rolling_force_n": rolling_force_n,
        "aerodynamic_force_n": aerodynamic_force_n,
        "rolling_power_w": rolling_power_w,
        "aerodynamic_power_w": aerodynamic_power_w,
        "traction_electrical_power_w": (
            traction_electrical_power_w
        ),
        "auxiliary_power_w": auxiliary_power_w,
        "total_demand_w": total_demand_w,
    }


# ============================================================
# 4. SOLAR ELECTRICAL POWER MODEL
# ============================================================

def calculate_solar_power(
    irradiance_w_m2,
    panel_area_m2=2.0,
    panel_efficiency=0.22,
    system_efficiency=0.95,
    shading_fraction=0.0,
):
    """
    Estimate solar electrical output in watts.

    Formula
    -------
    P = irradiance * area * panel efficiency
        * system efficiency * (1 - shading fraction)

    The output represents estimated electrical power after
    the configured system losses.

    Do not multiply this result by solar system efficiency
    a second time elsewhere in the energy balance.
    """

    irradiance_w_m2 = require_non_negative(
        irradiance_w_m2, "irradiance_w_m2"
    )
    panel_area_m2 = require_non_negative(
        panel_area_m2, "panel_area_m2"
    )
    panel_efficiency = require_fraction(
        panel_efficiency, "panel_efficiency"
    )
    system_efficiency = require_fraction(
        system_efficiency, "system_efficiency"
    )
    shading_fraction = require_fraction(
        shading_fraction, "shading_fraction"
    )

    return (
        irradiance_w_m2
        * panel_area_m2
        * panel_efficiency
        * system_efficiency
        * (1.0 - shading_fraction)
    )


# ============================================================
# 5. REGENERATIVE BRAKING ENERGY MODEL
# ============================================================

def calculate_regenerative_energy(
    previous_speed_mps,
    current_speed_mps,
    vehicle_mass_kg=1200.0,
    regenerative_efficiency=0.70,
    availability_factor=0.80,
    braking=False,
):
    """
    Estimate electrical energy recovered during a braking step.

    Kinetic energy:
        KE = 0.5 * mass * speed^2

    Estimated recovered energy:
        kinetic-energy reduction
        * availability factor
        * regenerative efficiency

    The braking flag must be True for this model to return
    recovered energy.

    This is a simplified estimate. It does not model actual
    motor torque, battery charge limits, brake blending,
    road loads during the braking event, or vehicle-specific
    regenerative power curves.
    """

    previous_speed_mps = require_non_negative(
        previous_speed_mps, "previous_speed_mps"
    )
    current_speed_mps = require_non_negative(
        current_speed_mps, "current_speed_mps"
    )
    vehicle_mass_kg = require_positive(
        vehicle_mass_kg, "vehicle_mass_kg"
    )
    regenerative_efficiency = require_fraction(
        regenerative_efficiency,
        "regenerative_efficiency",
    )
    availability_factor = require_fraction(
        availability_factor,
        "availability_factor",
    )

    # No regenerative energy is produced by this function
    # unless the step is explicitly identified as braking.
    if not braking:
        return {
            "kinetic_energy_reduction_kwh": 0.0,
            "recoverable_mechanical_energy_kwh": 0.0,
            "electrical_energy_kwh": 0.0,
            "conversion_loss_kwh": 0.0,
        }

    # The vehicle must be slowing down to have a positive
    # kinetic-energy reduction.
    if current_speed_mps >= previous_speed_mps:
        return {
            "kinetic_energy_reduction_kwh": 0.0,
            "recoverable_mechanical_energy_kwh": 0.0,
            "electrical_energy_kwh": 0.0,
            "conversion_loss_kwh": 0.0,
        }

    previous_ke_j = (
        0.5 * vehicle_mass_kg * previous_speed_mps ** 2
    )

    current_ke_j = (
        0.5 * vehicle_mass_kg * current_speed_mps ** 2
    )

    kinetic_reduction_j = max(
        0.0,
        previous_ke_j - current_ke_j,
    )

    # One kWh equals 3.6 million joules.
    kinetic_reduction_kwh = (
        kinetic_reduction_j / 3_600_000.0
    )

    # Account for the simplified fraction assumed available
    # to the regenerative system.
    recoverable_mechanical_kwh = (
        kinetic_reduction_kwh * availability_factor
    )

    # Apply regenerative conversion efficiency once.
    electrical_energy_kwh = (
        recoverable_mechanical_kwh
        * regenerative_efficiency
    )

    conversion_loss_kwh = (
        recoverable_mechanical_kwh
        - electrical_energy_kwh
    )

    return {
        "kinetic_energy_reduction_kwh": (
            kinetic_reduction_kwh
        ),
        "recoverable_mechanical_energy_kwh": (
            recoverable_mechanical_kwh
        ),
        "electrical_energy_kwh": electrical_energy_kwh,
        "conversion_loss_kwh": conversion_loss_kwh,
    }


# ============================================================
# 6. INITIALIZE THE SIMULATION
# ============================================================

def initialize_simulation(config=None):
    """
    Create a complete simulation state.

    Returns a dictionary containing:
    - Configuration.
    - Two Battery objects.
    - A BatteryManager.
    - Current simulation time and speed.
    - Energy, battery, and power histories.
    - Cumulative energy-accounting totals.
    """

    # Copy the defaults so modifying a scenario does not
    # permanently modify the global configuration.
    settings = dict(DEFAULT_CONFIG)

    if config is not None:
        settings.update(config)

    # Validate the core settings.
    settings["step_seconds"] = require_positive(
        settings["step_seconds"], "step_seconds"
    )

    settings["duration_seconds"] = require_positive(
        settings["duration_seconds"], "duration_seconds"
    )

    settings["vehicle_mass_kg"] = require_positive(
        settings["vehicle_mass_kg"], "vehicle_mass_kg"
    )

    settings["regenerative_efficiency"] = require_fraction(
        settings["regenerative_efficiency"],
        "regenerative_efficiency",
    )

    settings["braking_energy_availability_factor"] = (
        require_fraction(
            settings["braking_energy_availability_factor"],
            "braking_energy_availability_factor",
        )
    )

    # Create independent battery objects.
    battery_a = create_battery_a()
    battery_b = create_battery_b()

    # The Battery class supports a charging-efficiency setting.
    # Apply the scenario setting to both simulated batteries.
    charge_efficiency = require_fraction(
        settings["battery_charge_efficiency"],
        "battery_charge_efficiency",
    )

    if charge_efficiency <= 0:
        raise ValueError(
            "Battery charging efficiency must be greater than zero."
        )

    battery_a.charge_efficiency = charge_efficiency
    battery_b.charge_efficiency = charge_efficiency

    # The manager chooses and tracks the active battery.
    manager = BatteryManager(
        battery_a=battery_a,
        battery_b=battery_b,
        switch_threshold_percent=(
            settings["switch_threshold_percent"]
        ),
        hysteresis_percent=settings["hysteresis_percent"],
        min_switch_interval_seconds=0.0,
    )

    # Histories are lists of dictionaries, with one record
    # appended for each completed simulation step.
    state = {
        "config": settings,
        "batteries": {
            "A": battery_a,
            "B": battery_b,
        },
        "battery_manager": manager,
        "time_seconds": 0.0,
        "previous_speed_mps": require_non_negative(
            settings["initial_speed_mps"],
            "initial_speed_mps",
        ),
        "energy_history": [],
        "battery_history": [],
        "power_history": [],
        "event_history": [],
        "totals": {
            # Energy supplied by the solar model.
            "solar_generated_kwh": 0.0,

            # Electrical energy recovered from braking.
            "regenerative_electrical_kwh": 0.0,

            # Energy requested by the vehicle.
            "vehicle_demand_kwh": 0.0,

            # Energy removed from battery storage.
            "battery_energy_removed_kwh": 0.0,

            # Energy accepted at the battery charging input.
            "battery_charge_input_kwh": 0.0,

            # Energy actually added to battery storage.
            "battery_energy_stored_kwh": 0.0,

            # Charging conversion losses.
            "battery_charge_loss_kwh": 0.0,

            # Discharging conversion losses.
            "battery_discharge_loss_kwh": 0.0,

            # Regenerative conversion losses.
            "regenerative_conversion_loss_kwh": 0.0,

            # Energy available but neither used nor stored.
            "curtailed_solar_kwh": 0.0,
            "curtailed_regenerative_kwh": 0.0,

            # Sum of vehicle demand supplied by solar,
            # regenerative energy, and battery discharge.
            "solar_to_load_kwh": 0.0,
            "regenerative_to_load_kwh": 0.0,
            "battery_to_load_kwh": 0.0,
        },
    }

    return state


# ============================================================
# 7. BATTERY ENERGY HELPERS
# ============================================================

def _battery_available_energy_kwh(battery):
    """
    Return the battery's usable energy above its minimum SoC.

    The Battery class provides available_energy_kwh.
    This helper also prevents small negative floating-point
    results from entering the energy balance.
    """

    return max(
        0.0,
        float(battery.available_energy_kwh),
    )


def _battery_charge_input_limit_kwh(
    battery,
    requested_input_kwh,
    duration_seconds,
):
    """
    Estimate how much energy a battery can accept in this step.

    Limits:
    - Requested energy.
    - Remaining storage capacity, accounting for efficiency.
    - Maximum charging power over the time step.

    Returns the energy input that may be offered to add_energy().
    """

    requested_input_kwh = max(
        0.0,
        requested_input_kwh,
    )

    if requested_input_kwh <= 0.0:
        return 0.0

    # No charge can be accepted if the battery is unavailable.
    if not battery.is_available:
        return 0.0

    efficiency = float(battery.charge_efficiency)

    if efficiency <= 0.0:
        return 0.0

    remaining_capacity_kwh = max(
        0.0,
        float(battery.remaining_charge_capacity_kwh),
    )

    # Convert remaining storage capacity to an equivalent
    # maximum energy input before charging losses.
    capacity_input_limit_kwh = (
        remaining_capacity_kwh / efficiency
    )

    # The power limit is expressed in watts.
    maximum_charge_power_w = float(
        battery.max_charge_power_w
    )

    power_input_limit_kwh = (
        maximum_charge_power_w
        * duration_seconds
        / 3_600_000.0
    )

    return max(
        0.0,
        min(
            requested_input_kwh,
            capacity_input_limit_kwh,
            power_input_limit_kwh,
        ),
    )


def _charge_battery(
    battery,
    requested_input_kwh,
    duration_seconds,
):
    """
    Charge a battery and return measured accounting quantities.

    Battery.add_energy() is responsible for updating the
    battery's state of charge.

    The stored-energy difference is measured before and after
    the call, rather than assuming the entire requested input
    was accepted.
    """

    requested_input_kwh = max(
        0.0,
        requested_input_kwh,
    )

    offered_input_kwh = _battery_charge_input_limit_kwh(
        battery,
        requested_input_kwh,
        duration_seconds,
    )

    if offered_input_kwh <= 0.0:
        return {
            "input_kwh": 0.0,
            "stored_kwh": 0.0,
            "loss_kwh": 0.0,
            "unaccepted_kwh": requested_input_kwh,
        }

    stored_before_kwh = float(
        battery.stored_energy_kwh
    )

    # Apply charging efficiency in Battery.add_energy().
    battery.add_energy(
        offered_input_kwh,
        duration_s=duration_seconds,
        apply_charge_efficiency=True,
    )

    stored_after_kwh = float(
        battery.stored_energy_kwh
    )

    # The actual increase in stored energy is authoritative
    # for the simulation's accounting.
    stored_kwh = max(
        0.0,
        stored_after_kwh - stored_before_kwh,
    )

    efficiency = float(battery.charge_efficiency)

    # Infer the input energy corresponding to the observed
    # stored-energy increase.
    actual_input_kwh = min(
        offered_input_kwh,
        stored_kwh / efficiency if efficiency > 0 else 0.0,
    )

    # Small numerical differences are clamped to zero.
    loss_kwh = max(
        0.0,
        actual_input_kwh - stored_kwh,
    )

    unaccepted_kwh = max(
        0.0,
        requested_input_kwh - actual_input_kwh,
    )

    return {
        "input_kwh": actual_input_kwh,
        "stored_kwh": stored_kwh,
        "loss_kwh": loss_kwh,
        "unaccepted_kwh": unaccepted_kwh,
    }


def _discharge_battery(
    battery,
    requested_load_energy_kwh,
    duration_seconds,
):
    """
    Remove energy from battery storage to supply vehicle load.

    The Battery.consume_energy() method updates the battery's
    SoC and cumulative energy-consumption counter.

    This simplified model treats consume_energy() as removing
    stored energy. It accounts for the difference between
    stored energy removed and useful load energy delivered as
    a discharge/conversion loss.
    """

    requested_load_energy_kwh = max(
        0.0,
        requested_load_energy_kwh,
    )

    if requested_load_energy_kwh <= 0.0:
        return {
            "load_supplied_kwh": 0.0,
            "stored_removed_kwh": 0.0,
            "loss_kwh": 0.0,
            "unmet_load_kwh": 0.0,
        }

    if not battery.is_available():
        return {
            "load_supplied_kwh": 0.0,
            "stored_removed_kwh": 0.0,
            "loss_kwh": 0.0,
            "unmet_load_kwh": requested_load_energy_kwh,
        }

    # Maximum discharge power over this step, converted to kWh.
    maximum_discharge_kwh = (
        float(battery.max_discharge_power_w)
        * duration_seconds
        / 3_600_000.0
    )

    # Available stored energy is measured above the configured
    # minimum SoC, not the battery's total stored energy.
    available_stored_kwh = _battery_available_energy_kwh(
        battery
    )

    # To deliver the requested useful load energy, the model
    # needs a corresponding amount removed from storage.
    # This simplified model uses 95% discharge efficiency.
    discharge_efficiency = 0.95

    required_stored_kwh = (
        requested_load_energy_kwh
        / discharge_efficiency
    )

    stored_to_remove_kwh = min(
        available_stored_kwh,
        maximum_discharge_kwh,
        required_stored_kwh,
    )

    if stored_to_remove_kwh <= 0.0:
        return {
            "load_supplied_kwh": 0.0,
            "stored_removed_kwh": 0.0,
            "loss_kwh": 0.0,
            "unmet_load_kwh": requested_load_energy_kwh,
        }

    stored_before_kwh = float(
        battery.stored_energy_kwh
    )

    # Remove energy from the battery.
    #
    # The Battery class enforces its own SoC and power checks.
    try:
        battery.consume_energy(
            stored_to_remove_kwh,
            duration_s=duration_seconds,
        )
    except (ValueError, RuntimeError):
        # If the Battery class rejects the operation, do not
        # claim that any energy was delivered.
        return {
            "load_supplied_kwh": 0.0,
            "stored_removed_kwh": 0.0,
            "loss_kwh": 0.0,
            "unmet_load_kwh": requested_load_energy_kwh,
        }

    stored_after_kwh = float(
        battery.stored_energy_kwh
    )

    actual_stored_removed_kwh = max(
        0.0,
        stored_before_kwh - stored_after_kwh,
    )

    # Useful electrical energy delivered to the load.
    load_supplied_kwh = min(
        requested_load_energy_kwh,
        actual_stored_removed_kwh * discharge_efficiency,
    )

    loss_kwh = max(
        0.0,
        actual_stored_removed_kwh - load_supplied_kwh,
    )

    unmet_load_kwh = max(
        0.0,
        requested_load_energy_kwh - load_supplied_kwh,
    )

    return {
        "load_supplied_kwh": load_supplied_kwh,
        "stored_removed_kwh": actual_stored_removed_kwh,
        "loss_kwh": loss_kwh,
        "unmet_load_kwh": unmet_load_kwh,
    }


# ============================================================
# 8. ENERGY BALANCE UPDATE
# ============================================================

def update_energy_balance(
    state,
    solar_energy_kwh,
    regenerative_energy_kwh,
    vehicle_demand_kwh,
    duration_seconds,
):
    """
    Allocate the available energy and update battery states.

    Allocation order
    ----------------
    1. Solar energy supplies vehicle demand first.
    2. Regenerative electrical energy supplies any remaining
       vehicle demand.
    3. The active battery supplies any remaining demand.
    4. Remaining solar energy is offered to the active battery.
    5. Remaining regenerative energy is offered to the active
       battery.
    6. Unaccepted surplus is recorded as curtailed energy.

    Charging losses are tracked separately from stored energy.

    Energy-balance convention
    -------------------------
    Inputs:
        solar energy + regenerative electrical energy
        + energy removed from battery storage

    Outputs:
        vehicle load + energy stored in batteries
        + conversion losses + curtailed energy

    Therefore:
        inputs - outputs = balance error

    The error should be close to zero, subject to numerical
    precision and the simplifications of this model.
    """

    solar_energy_kwh = require_non_negative(
        solar_energy_kwh, "solar_energy_kwh"
    )

    regenerative_energy_kwh = require_non_negative(
        regenerative_energy_kwh,
        "regenerative_energy_kwh",
    )

    vehicle_demand_kwh = require_non_negative(
        vehicle_demand_kwh,
        "vehicle_demand_kwh",
    )

    duration_seconds = require_positive(
        duration_seconds, "duration_seconds"
    )

    batteries = state["batteries"]
    manager = state["battery_manager"]
    totals = state["totals"]

    # These are the energy sources available during this step.
    solar_remaining_kwh = solar_energy_kwh
    regenerative_remaining_kwh = regenerative_energy_kwh

    # Per-step counters begin at zero.
    step = {
        "solar_to_load_kwh": 0.0,
        "regenerative_to_load_kwh": 0.0,
        "battery_to_load_kwh": 0.0,
        "battery_energy_removed_kwh": 0.0,
        "battery_charge_input_kwh": 0.0,
        "battery_energy_stored_kwh": 0.0,
        "battery_charge_loss_kwh": 0.0,
        "battery_discharge_loss_kwh": 0.0,
        "curtailed_solar_kwh": 0.0,
        "curtailed_regenerative_kwh": 0.0,
        "unmet_vehicle_demand_kwh": 0.0,
    }

    # --------------------------------------------------------
    # A. Use solar energy directly for vehicle demand.
    # --------------------------------------------------------

    solar_to_load = min(
        solar_remaining_kwh,
        vehicle_demand_kwh,
    )

    solar_remaining_kwh -= solar_to_load

    remaining_demand_kwh = (
        vehicle_demand_kwh - solar_to_load
    )

    step["solar_to_load_kwh"] = solar_to_load

    # --------------------------------------------------------
    # B. Use recovered regenerative energy for remaining load.
    # --------------------------------------------------------

    regenerative_to_load = min(
        regenerative_remaining_kwh,
        remaining_demand_kwh,
    )

    regenerative_remaining_kwh -= regenerative_to_load

    remaining_demand_kwh -= regenerative_to_load

    step["regenerative_to_load_kwh"] = (
        regenerative_to_load
    )

    # --------------------------------------------------------
    # C. Ask the battery manager for the active battery.
    # --------------------------------------------------------

    manager.update()

    active_id = manager.active_battery_id

    # If a switch happened or the active battery is unavailable,
    # use the manager's latest selection.
    active_battery = (
        batteries[active_id]
        if active_id in batteries
        else None
    )

    # --------------------------------------------------------
    # D. Supply the remaining demand from battery storage.
    # --------------------------------------------------------

    if remaining_demand_kwh > 0.0 and active_battery is not None:

        discharge_result = _discharge_battery(
            active_battery,
            remaining_demand_kwh,
            duration_seconds,
        )

        step["battery_to_load_kwh"] = (
            discharge_result["load_supplied_kwh"]
        )

        step["battery_energy_removed_kwh"] = (
            discharge_result["stored_removed_kwh"]
        )

        step["battery_discharge_loss_kwh"] = (
            discharge_result["loss_kwh"]
        )

        remaining_demand_kwh = (
            discharge_result["unmet_load_kwh"]
        )

    # Record demand that none of the simulated sources supplied.
    step["unmet_vehicle_demand_kwh"] = max(
        0.0,
        remaining_demand_kwh,
    )

    # --------------------------------------------------------
    # E. Charge the active battery with remaining solar energy.
    # --------------------------------------------------------

    if solar_remaining_kwh > 0.0 and active_battery is not None:

        charge_result = _charge_battery(
            active_battery,
            solar_remaining_kwh,
            duration_seconds,
        )

        step["battery_charge_input_kwh"] += (
            charge_result["input_kwh"]
        )

        step["battery_energy_stored_kwh"] += (
            charge_result["stored_kwh"]
        )

        step["battery_charge_loss_kwh"] += (
            charge_result["loss_kwh"]
        )

        solar_remaining_kwh = (
            charge_result["unaccepted_kwh"]
        )

    # --------------------------------------------------------
    # F. Charge the active battery with remaining regenerative
    #    energy.
    # --------------------------------------------------------

    if (
        regenerative_remaining_kwh > 0.0
        and active_battery is not None
    ):

        charge_result = _charge_battery(
            active_battery,
            regenerative_remaining_kwh,
            duration_seconds,
        )

        step["battery_charge_input_kwh"] += (
            charge_result["input_kwh"]
        )

        step["battery_energy_stored_kwh"] += (
            charge_result["stored_kwh"]
        )

        step["battery_charge_loss_kwh"] += (
            charge_result["loss_kwh"]
        )

        regenerative_remaining_kwh = (
            charge_result["unaccepted_kwh"]
        )

    # --------------------------------------------------------
    # G. Record energy that could not be used or stored.
    # --------------------------------------------------------

    step["curtailed_solar_kwh"] = max(
        0.0,
        solar_remaining_kwh,
    )

    step["curtailed_regenerative_kwh"] = max(
        0.0,
        regenerative_remaining_kwh,
    )

    # --------------------------------------------------------
    # H. Compute the balance error for this step.
    # --------------------------------------------------------

    # Solar and regenerative energy not sent to the load are
    # either accepted by the battery or curtailed.
    #
    # Battery charge input is an internal flow from the source
    # bus to battery storage; its stored portion and conversion
    # loss are outputs in the energy balance.

    input_energy_kwh = (
        solar_energy_kwh
        + regenerative_energy_kwh
        + step["battery_energy_removed_kwh"]
    )

    output_energy_kwh = (
        step["solar_to_load_kwh"]
        + step["regenerative_to_load_kwh"]
        + step["battery_to_load_kwh"]
        + step["battery_energy_stored_kwh"]
        + step["battery_charge_loss_kwh"]
        + step["battery_discharge_loss_kwh"]
        + step["curtailed_solar_kwh"]
        + step["curtailed_regenerative_kwh"]
    )

    # The balance error is diagnostic. A significant nonzero
    # result suggests an accounting or state-update problem.
    balance_error_kwh = (
        input_energy_kwh - output_energy_kwh
    )

    step["input_energy_kwh"] = input_energy_kwh
    step["output_energy_kwh"] = output_energy_kwh
    step["balance_error_kwh"] = balance_error_kwh

    # --------------------------------------------------------
    # I. Update cumulative totals.
    # --------------------------------------------------------

    totals["solar_generated_kwh"] += solar_energy_kwh

    totals["regenerative_electrical_kwh"] += (
        regenerative_energy_kwh
    )

    totals["vehicle_demand_kwh"] += vehicle_demand_kwh

    totals["battery_energy_removed_kwh"] += (
        step["battery_energy_removed_kwh"]
    )

    totals["battery_charge_input_kwh"] += (
        step["battery_charge_input_kwh"]
    )

    totals["battery_energy_stored_kwh"] += (
        step["battery_energy_stored_kwh"]
    )

    totals["battery_charge_loss_kwh"] += (
        step["battery_charge_loss_kwh"]
    )

    totals["battery_discharge_loss_kwh"] += (
        step["battery_discharge_loss_kwh"]
    )

    totals["curtailed_solar_kwh"] += (
        step["curtailed_solar_kwh"]
    )

    totals["curtailed_regenerative_kwh"] += (
        step["curtailed_regenerative_kwh"]
    )

    totals["solar_to_load_kwh"] += (
        step["solar_to_load_kwh"]
    )

    totals["regenerative_to_load_kwh"] += (
        step["regenerative_to_load_kwh"]
    )

    totals["battery_to_load_kwh"] += (
        step["battery_to_load_kwh"]
    )

    return step


# ============================================================
# 9. RUN ONE SIMULATION STEP
# ============================================================

def run_simulation_step(
    state,
    speed_mps,
    irradiance_w_m2,
    braking=False,
):
    """
    Simulate one time step.

    Inputs
    ------
    state:
        Dictionary returned by initialize_simulation().

    speed_mps:
        Current vehicle speed in m/s.

    irradiance_w_m2:
        Solar irradiance in W/m² for this step.

    braking:
        Set True if this step represents a braking event.

    Returns
    -------
    dict
        A record of power, energy, battery state, and balance.

    Important
    ---------
    Speed is supplied by the scenario. This function does not
    generate a realistic drive cycle by itself.
    """

    config = state["config"]

    dt = config["step_seconds"]

    speed_mps = require_non_negative(
        speed_mps, "speed_mps"
    )

    irradiance_w_m2 = require_non_negative(
        irradiance_w_m2, "irradiance_w_m2"
    )

    previous_speed_mps = state["previous_speed_mps"]

    # --------------------------------------------------------
    # A. Calculate vehicle load power.
    # --------------------------------------------------------

    load = calculate_load(
        speed_mps=speed_mps,
        vehicle_mass_kg=config["vehicle_mass_kg"],
        drag_coefficient=config["drag_coefficient"],
        frontal_area_m2=config["frontal_area_m2"],
        air_density_kg_m3=config["air_density_kg_m3"],
        rolling_resistance_coefficient=(
            config["rolling_resistance_coefficient"]
        ),
        drivetrain_efficiency=(
            config["drivetrain_efficiency"]
        ),
        auxiliary_power_w=config["auxiliary_power_w"],
    )

    # Convert watts into energy for this step:
    # kWh = W * seconds / 3,600,000.
    vehicle_demand_kwh = (
        load["total_demand_w"] * dt / 3_600_000.0
    )

    # --------------------------------------------------------
    # B. Calculate solar electrical power and energy.
    # --------------------------------------------------------

    solar_power_w = calculate_solar_power(
        irradiance_w_m2=irradiance_w_m2,
        panel_area_m2=config["solar_panel_area_m2"],
        panel_efficiency=config["solar_panel_efficiency"],
        system_efficiency=config["solar_system_efficiency"],
        shading_fraction=config["solar_shading_fraction"],
    )

    solar_energy_kwh = (
        solar_power_w * dt / 3_600_000.0
    )

    # --------------------------------------------------------
    # C. Calculate regenerative electrical energy.
    # --------------------------------------------------------

    regen = calculate_regenerative_energy(
        previous_speed_mps=previous_speed_mps,
        current_speed_mps=speed_mps,
        vehicle_mass_kg=config["vehicle_mass_kg"],
        regenerative_efficiency=(
            config["regenerative_efficiency"]
        ),
        availability_factor=(
            config["braking_energy_availability_factor"]
        ),
        braking=braking,
    )

    regenerative_energy_kwh = (
        regen["electrical_energy_kwh"]
    )

    # --------------------------------------------------------
    # D. Allocate energy and update the battery state.
    # --------------------------------------------------------

    energy_result = update_energy_balance(
        state=state,
        solar_energy_kwh=solar_energy_kwh,
        regenerative_energy_kwh=regenerative_energy_kwh,
        vehicle_demand_kwh=vehicle_demand_kwh,
        duration_seconds=dt,
    )

    # --------------------------------------------------------
    # E. Record power history.
    # --------------------------------------------------------

    # Average regenerative power is the recovered electrical
    # energy divided by the time-step duration.
    regenerative_power_w = (
        regenerative_energy_kwh
        * 3_600_000.0
        / dt
    )

    # Average solar power follows the same unit conversion.
    solar_average_power_w = (
        solar_energy_kwh
        * 3_600_000.0
        / dt
    )

    time_end_seconds = (
        state["time_seconds"] + dt
    )

    power_record = {
        "time_seconds": time_end_seconds,
        "speed_mps": speed_mps,
        "speed_kmh": speed_mps * 3.6,
        "irradiance_w_m2": irradiance_w_m2,
        "solar_power_w": solar_average_power_w,
        "regenerative_power_w": regenerative_power_w,
        "vehicle_demand_w": load["total_demand_w"],
        "traction_power_w": (
            load["traction_electrical_power_w"]
        ),
        "auxiliary_power_w": load["auxiliary_power_w"],
    }

    state["power_history"].append(power_record)

    # --------------------------------------------------------
    # F. Record the energy history.
    # --------------------------------------------------------

    energy_record = {
        "time_seconds": time_end_seconds,
        "solar_generated_kwh": solar_energy_kwh,
        "regenerative_electrical_kwh": (
            regenerative_energy_kwh
        ),
        "vehicle_demand_kwh": vehicle_demand_kwh,
        "solar_to_load_kwh": (
            energy_result["solar_to_load_kwh"]
        ),
        "regenerative_to_load_kwh": (
            energy_result["regenerative_to_load_kwh"]
        ),
        "battery_to_load_kwh": (
            energy_result["battery_to_load_kwh"]
        ),
        "battery_energy_removed_kwh": (
            energy_result["battery_energy_removed_kwh"]
        ),
        "battery_charge_input_kwh": (
            energy_result["battery_charge_input_kwh"]
        ),
        "battery_energy_stored_kwh": (
            energy_result["battery_energy_stored_kwh"]
        ),
        "battery_charge_loss_kwh": (
            energy_result["battery_charge_loss_kwh"]
        ),
        "battery_discharge_loss_kwh": (
            energy_result["battery_discharge_loss_kwh"]
        ),
        "curtailed_solar_kwh": (
            energy_result["curtailed_solar_kwh"]
        ),
        "curtailed_regenerative_kwh": (
            energy_result["curtailed_regenerative_kwh"]
        ),
        "unmet_vehicle_demand_kwh": (
            energy_result["unmet_vehicle_demand_kwh"]
        ),
        "balance_error_kwh": (
            energy_result["balance_error_kwh"]
        ),
    }

    state["energy_history"].append(energy_record)

    # --------------------------------------------------------
    # G. Record battery history.
    # --------------------------------------------------------

    manager = state["battery_manager"]

    battery_record = {
        "time_seconds": time_end_seconds,
        "active_battery_id": (
            manager.active_battery_id or ""
        ),
        "controller_status": manager.controller_status,
        "battery_a_soc_percent": (
            state["batteries"]["A"].soc_percent
        ),
        "battery_b_soc_percent": (
            state["batteries"]["B"].soc_percent
        ),
        "battery_a_stored_kwh": (
            state["batteries"]["A"].stored_energy_kwh
        ),
        "battery_b_stored_kwh": (
            state["batteries"]["B"].stored_energy_kwh
        ),
        "battery_a_available_kwh": (
            state["batteries"]["A"].available_energy_kwh
        ),
        "battery_b_available_kwh": (
            state["batteries"]["B"].available_energy_kwh
        ),
    }

    state["battery_history"].append(battery_record)

    # --------------------------------------------------------
    # H. Save the step and advance the simulation clock.
    # --------------------------------------------------------

    state["time_seconds"] = time_end_seconds

    state["previous_speed_mps"] = speed_mps

    # Add the manager's latest event if it has generated one.
    if manager.switching_events:
        latest_event = manager.switching_events[-1]

        # Avoid duplicating the same event in this history.
        if (
            not state["event_history"]
            or state["event_history"][-1] != latest_event
        ):
            state["event_history"].append(
                dict(latest_event)
            )

    # Return a useful combined step result.
    return {
        "time_seconds": time_end_seconds,
        "load": load,
        "solar_power_w": solar_power_w,
        "solar_energy_kwh": solar_energy_kwh,
        "regenerative": regen,
        "energy": energy_result,
        "battery": battery_record,
        "power": power_record,
    }


# ============================================================
# 10. RUN A COMPLETE SIMULATION
# ============================================================

def run_simulation(
    config=None,
    drive_cycle=None,
    irradiance_profile=None,
    braking_profile=None,
):
    """
    Run a complete simulation.

    Parameters
    ----------
    config:
        Optional dictionary overriding DEFAULT_CONFIG.

    drive_cycle:
        Optional list of vehicle speeds in m/s, one per step.

    irradiance_profile:
        Optional list of irradiance values in W/m², one per step.

    braking_profile:
        Optional list of booleans indicating braking steps.

    If profiles are omitted:
        - Speed defaults to the configured initial speed.
        - Irradiance defaults to zero.
        - Braking defaults to False.

    This default is intentionally conservative: it does not
    invent a driving cycle or sunlight profile.
    """
    from data_logger import DataLogger

    state = initialize_simulation(config)

    config = state["config"]

    dt = config["step_seconds"]
    duration = config["duration_seconds"]

    number_of_steps = int(math.ceil(duration / dt))

    # Validate that supplied profiles cover every simulation
    # step. Profiles can be generated by a separate scenario
    # module or supplied manually.
    if drive_cycle is not None:
        if len(drive_cycle) < number_of_steps:
            raise ValueError(
                "drive_cycle must contain at least one speed "
                "for every simulation step."
            )

    if irradiance_profile is not None:
        if len(irradiance_profile) < number_of_steps:
            raise ValueError(
                "irradiance_profile must contain at least one "
                "irradiance value for every simulation step."
            )

    if braking_profile is not None:
        if len(braking_profile) < number_of_steps:
            raise ValueError(
                "braking_profile must contain at least one "
                "boolean for every simulation step."
            )

    # --------------------------------------------------------
    # Execute the simulation loop.
    # --------------------------------------------------------
    logger = DataLogger()
    next_event_index = 0
    for index in range(number_of_steps):

        # Shorten the final step if the duration is not an
        # exact multiple of the configured time step.
        remaining_seconds = (
            duration - state["time_seconds"]
        )

        actual_dt = min(dt, remaining_seconds)

        if actual_dt <= 0.0:
            break

        # The module's state uses a fixed step size. For a
        # shorter final step, temporarily override the setting.
        original_dt = config["step_seconds"]
        config["step_seconds"] = actual_dt

        try:
            # Read the driving profile or use a stationary
            # default speed.
            speed = (
                drive_cycle[index]
                if drive_cycle is not None
                else config["initial_speed_mps"]
            )

            # Read solar irradiance or default to zero sunlight.
            irradiance = (
                irradiance_profile[index]
                if irradiance_profile is not None
                else 0.0
            )

            # A braking profile explicitly identifies steps
            # in which regenerative recovery is permitted.
            braking = (
                braking_profile[index]
                if braking_profile is not None
                else False
            )

            run_simulation_step(
                state=state,
                speed_mps=speed,
                irradiance_w_m2=irradiance,
                braking=braking,
            )
            # Record this simulation step
            logger.record_simulation_step(
                stat_result,
                simulation_state=state
            )

            # Import any new battery-switching events
            manager = state["battery_manager"]

            next_event_index = logger.import_battery_manager_events(
                manager,
                start_index=next_event_index
            )

        finally:
            # Restore the configured time step.
            config["step_seconds"] = original_dt
    logger.save_csv()

    # Attach summary metrics after the loop finishes.
    state["summary"] = calculate_summary(state)


    return state


# ============================================================
# 11. CALCULATE SUMMARY METRICS
# ============================================================

def calculate_summary(state):
    """
    Calculate summary metrics for a completed simulation.
    """

    totals = state["totals"]

    total_demand = totals["vehicle_demand_kwh"]

    total_solar = totals["solar_generated_kwh"]

    total_regen = totals["regenerative_electrical_kwh"]

    total_battery_removed = (
        totals["battery_energy_removed_kwh"]
    )

    total_battery_stored = (
        totals["battery_energy_stored_kwh"]
    )

    total_unmet_demand = sum(
        record["unmet_vehicle_demand_kwh"]
        for record in state["energy_history"]
    )

    # The total load supplied is the sum of direct solar,
    # direct regenerative energy, and battery-delivered energy.
    total_load_supplied = (
        totals["solar_to_load_kwh"]
        + totals["regenerative_to_load_kwh"]
        + totals["battery_to_load_kwh"]
    )

    # A load coverage ratio is useful for scenario comparison.
    if total_demand > 0:
        load_coverage_ratio = (
            total_load_supplied / total_demand
        )
    else:
        load_coverage_ratio = 1.0

    # Energy remaining in both batteries at the end.
    final_stored_energy = sum(
        battery.stored_energy_kwh
        for battery in state["batteries"].values()
    )

    initial_stored_energy = sum(
        record["stored_kwh"]
        for record in state.get(
            "initial_battery_snapshot",
            [],
        )
    )

    # The initial snapshot is populated by the runner below
    # when present. If absent, do not invent a value.
    if not initial_stored_energy:
        initial_stored_energy = None

    return {
        "simulation_duration_seconds": (
            state["time_seconds"]
        ),
        "simulation_steps": len(
            state["energy_history"]
        ),
        "solar_generated_kwh": total_solar,
        "regenerative_electrical_kwh": total_regen,
        "vehicle_demand_kwh": total_demand,
        "load_supplied_kwh": total_load_supplied,
        "unmet_vehicle_demand_kwh": total_unmet_demand,
        "load_coverage_percent": (
            load_coverage_ratio * 100.0
        ),
        "battery_energy_removed_kwh": (
            total_battery_removed
        ),
        "battery_energy_stored_kwh": (
            total_battery_stored
        ),
        "battery_charge_loss_kwh": (
            totals["battery_charge_loss_kwh"]
        ),
        "battery_discharge_loss_kwh": (
            totals["battery_discharge_loss_kwh"]
        ),
        "curtailed_solar_kwh": (
            totals["curtailed_solar_kwh"]
        ),
        "curtailed_regenerative_kwh": (
            totals["curtailed_regenerative_kwh"]
        ),
        "final_battery_energy_kwh": final_stored_energy,
        "initial_battery_energy_kwh": initial_stored_energy,
        "switching_event_count": len(
            state["battery_manager"].switching_events
        ),
        "mean_balance_error_kwh": (
            sum(
                record["balance_error_kwh"]
                for record in state["energy_history"]
            )
            / len(state["energy_history"])
            if state["energy_history"]
            else 0.0
        ),
        "maximum_absolute_step_balance_error_kwh": (
            max(
                (
                    abs(record["balance_error_kwh"])
                    for record in state["energy_history"]
                ),
                default=0.0,
            )
        ),
    }


# ============================================================
# 12. PRINT THE SIMULATION SUMMARY
# ============================================================

def print_summary(state):
    """Print the simulation's main results."""

    summary = state.get("summary")

    if summary is None:
        summary = calculate_summary(state)

    print("\n" + "=" * 66)
    print("FLUXXWAVE — ENERGY SIMULATION SUMMARY")
    print("=" * 66)

    print(
        f"Simulation duration: "
        f"{summary['simulation_duration_seconds']:.1f} seconds"
    )

    print(
        f"Simulation steps: "
        f"{summary['simulation_steps']}"
    )

    print("\nENERGY")

    print(
        f"Solar generated: "
        f"{summary['solar_generated_kwh']:.6f} kWh"
    )

    print(
        f"Regenerative electrical energy: "
        f"{summary['regenerative_electrical_kwh']:.6f} kWh"
    )

    print(
        f"Vehicle demand: "
        f"{summary['vehicle_demand_kwh']:.6f} kWh"
    )

    print(
        f"Load supplied: "
        f"{summary['load_supplied_kwh']:.6f} kWh"
    )

    print(
        f"Unmet demand: "
        f"{summary['unmet_vehicle_demand_kwh']:.6f} kWh"
    )

    print(
        f"Load coverage: "
        f"{summary['load_coverage_percent']:.2f}%"
    )

    print("\nBATTERIES")

    print(
        f"Energy removed from storage: "
        f"{summary['battery_energy_removed_kwh']:.6f} kWh"
    )

    print(
        f"Energy added to storage: "
        f"{summary['battery_energy_stored_kwh']:.6f} kWh"
    )

    print(
        f"Final combined stored energy: "
        f"{summary['final_battery_energy_kwh']:.6f} kWh"
    )

    print("\nLOSSES AND CURTAILMENT")

    print(
        f"Charging losses: "
        f"{summary['battery_charge_loss_kwh']:.6f} kWh"
    )

    print(
        f"Discharging losses: "
        f"{summary['battery_discharge_loss_kwh']:.6f} kWh"
    )

    print(
        f"Curtailed solar energy: "
        f"{summary['curtailed_solar_kwh']:.6f} kWh"
    )

    print(
        f"Curtailed regenerative energy: "
        f"{summary['curtailed_regenerative_kwh']:.6f} kWh"
    )

    print("\nENERGY BALANCE CHECK")

    print(
        f"Mean step balance error: "
        f"{summary['mean_balance_error_kwh']:.12f} kWh"
    )

    print(
        f"Maximum absolute step error: "
        f"{summary['maximum_absolute_step_balance_error_kwh']:.12f} kWh"
    )

    print("\nBATTERY STATE")

    state["battery_manager"].print_status()

    print("=" * 66)


# ============================================================
# 13. EXPORT HISTORIES TO CSV
# ============================================================

def export_history_to_csv(
    state,
    output_directory="data/energy_simulation",
):
    """
    Export the simulation histories to separate CSV files.

    Files created:
        energy_history.csv
        battery_history.csv
        power_history.csv
        switching_events.csv

    Returns a dictionary of output file paths.
    """

    output_dir = Path(output_directory)

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    datasets = {
        "energy": state["energy_history"],
        "battery": state["battery_history"],
        "power": state["power_history"],
        "events": state["event_history"],
    }

    output_paths = {}

    for dataset_name, rows in datasets.items():

        filename = f"{dataset_name}_history.csv"

        # Use a more explicit name for the switching log.
        if dataset_name == "events":
            filename = "switching_events.csv"

        path = output_dir / filename

        # An empty history has no field names to write.
        if not rows:
            output_paths[dataset_name] = str(path)
            continue

        fieldnames = list(rows[0].keys())

        with path.open(
            mode="w",
            newline="",
            encoding="utf-8",
        ) as csv_file:

            writer = csv.DictWriter(
                csv_file,
                fieldnames=fieldnames,
            )

            writer.writeheader()
            writer.writerows(rows)

        output_paths[dataset_name] = str(path)

    print("\nSimulation histories exported:")

    for dataset_name, path in output_paths.items():
        print(f"  {dataset_name}: {path}")

    return output_paths


# ============================================================
# 14. SCENARIO COMPARISON
# ============================================================

def compare_scenarios(scenarios):
    """
    Run multiple scenarios and compare their summary metrics.

    Parameters
    ----------
    scenarios:
        Dictionary of scenario names to dictionaries.

    Example
    -------
    scenarios = {
        "baseline": {
            "config": {"auxiliary_power_w": 300},
            "drive_cycle": [...],
            "irradiance_profile": [...],
            "braking_profile": [...],
        },
        "higher_solar": {
            "config": {"solar_panel_area_m2": 3.0},
            "drive_cycle": [...],
            "irradiance_profile": [...],
            "braking_profile": [...],
        },
    }

    Each scenario can override configuration and provide
    its own driving, sunlight, and braking profiles.
    """

    results = {}

    for scenario_name, scenario in scenarios.items():

        results[scenario_name] = run_simulation(
            config=scenario.get("config"),
            drive_cycle=scenario.get("drive_cycle"),
            irradiance_profile=scenario.get(
                "irradiance_profile"
            ),
            braking_profile=scenario.get(
                "braking_profile"
            ),
        )

    return results


def print_scenario_comparison(results):
    """Print a compact comparison of completed scenarios."""

    print("\n" + "=" * 92)
    print("FLUXXWAVE — SCENARIO COMPARISON")
    print("=" * 92)

    print(
        f"{'Scenario':<22}"
        f"{'Solar (kWh)':>14}"
        f"{'Regen (kWh)':>14}"
        f"{'Demand (kWh)':>15}"
        f"{'Unmet (kWh)':>14}"
        f"{'Coverage %':>12}"
    )

    print("-" * 92)

    for name, state in results.items():

        summary = state.get("summary") or calculate_summary(
            state
        )

        print(
            f"{name:<22}"
            f"{summary['solar_generated_kwh']:>14.5f}"
            f"{summary['regenerative_electrical_kwh']:>14.5f}"
            f"{summary['vehicle_demand_kwh']:>15.5f}"
            f"{summary['unmet_vehicle_demand_kwh']:>14.5f}"
            f"{summary['load_coverage_percent']:>12.2f}"
        )

    print("=" * 92)


# ============================================================
# 15. EXAMPLE SCENARIO
# ============================================================

def create_demo_profiles(number_of_steps, step_seconds):
    """
    Create simple, illustrative profiles for testing.

    The drive cycle is deliberately synthetic. It is not a
    measured real-world driving cycle.

    The vehicle:
    - Starts stationary.
    - Accelerates to a moderate speed.
    - Cruises.
    - Brakes to a stop.
    - Repeats a simple pattern.

    Solar irradiance follows a basic daytime pattern for the
    purpose of demonstration.
    """

    drive_cycle = []
    irradiance_profile = []
    braking_profile = []

    for index in range(number_of_steps):

        time_seconds = index * step_seconds

        # A short synthetic speed cycle.
        cycle_position = index % 12

        if cycle_position < 3:
            speed_mps = 5.0 + cycle_position * 2.0
        elif cycle_position < 8:
            speed_mps = 11.0
        elif cycle_position < 10:
            speed_mps = 7.0
        else:
            speed_mps = 3.0

        # The profile explicitly identifies the step in which
        # the vehicle is slowing under braking.
        previous_position = (index - 1) % 12

        braking = (
            index > 0
            and cycle_position in (8, 9, 10, 11)
            and cycle_position > previous_position
        )

        # A simple daylight profile over a 24-hour cycle.
        # This example compresses time only if the configured
        # simulation step is interpreted as seconds of a
        # notional simulation clock.
        simulated_hour = (
            (time_seconds / 3600.0) % 24.0
        )

        if 6.0 <= simulated_hour <= 18.0:

            daylight_fraction = (
                (simulated_hour - 6.0) / 12.0
            )

            irradiance = (
                900.0
                * math.sin(math.pi * daylight_fraction)
            )

            irradiance = max(0.0, irradiance)

        else:
            irradiance = 0.0

        drive_cycle.append(speed_mps)
        irradiance_profile.append(irradiance)
        braking_profile.append(braking)

    return (
        drive_cycle,
        irradiance_profile,
        braking_profile,
    )


# ============================================================
# 16. MAIN ENTRY POINT
# ============================================================

def main():
    """
    Run the example simulation, display the summary, and
    export its histories.
    """

    # A short demonstration run.
    demo_config = {
        "step_seconds": 60.0,
        "duration_seconds": 3600.0,
        "initial_speed_mps": 0.0,
    }

    number_of_steps = int(
        math.ceil(
            demo_config["duration_seconds"]
            / demo_config["step_seconds"]
        )
    )

    (
        drive_cycle,
        irradiance_profile,
        braking_profile,
    ) = create_demo_profiles(
        number_of_steps,
        demo_config["step_seconds"],
    )

    state = run_simulation(
        config=demo_config,
        drive_cycle=drive_cycle,
        irradiance_profile=irradiance_profile,
        braking_profile=braking_profile,
    )

    print_summary(state)

    export_history_to_csv(state)

    # A separate scenario can change assumptions while keeping
    # the same drive and sunlight profiles.
    comparison_scenarios = {
        "Baseline": {
            "config": demo_config,
            "drive_cycle": drive_cycle,
            "irradiance_profile": irradiance_profile,
            "braking_profile": braking_profile,
        },
        "Larger Solar Array": {
            "config": {
                **demo_config,
                "solar_panel_area_m2": 3.0,
            },
            "drive_cycle": drive_cycle,
            "irradiance_profile": irradiance_profile,
            "braking_profile": braking_profile,
        },
    }

    comparison_results = compare_scenarios(
        comparison_scenarios
    )

    print_scenario_comparison(
        comparison_results
    )


if __name__ == "__main__":
    main()
