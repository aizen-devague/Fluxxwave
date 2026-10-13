
"""
FLUXXWAVE — REGENERATIVE ENERGY RECOVERY MODEL
==============================================

Project:
    Fluxxwave — Solar-Assisted Electric Vehicle Concept

Purpose:
    Mathematically model the kinetic energy available during vehicle
    deceleration and estimate the electrical energy recoverable through
    a hypothetical regenerative braking system.

CORE CAPABILITIES
-----------------
1. Calculate translational kinetic energy.
2. Calculate energy changes between two vehicle speeds.
3. Estimate mechanical energy available for recovery.
4. Estimate electrical energy returned to storage.
5. Account for simplified drivetrain conversion losses.
6. Estimate average braking power and recovered electrical power.
7. Optionally account for rotational kinetic energy.
8. Simulate a sequence of speed measurements.
9. Analyse repeated braking events.
10. Export results to CSV.
11. Plot energy, speed, power, and recovery data.
12. Generate a detailed text report.

PHYSICAL PRINCIPLE
------------------
Kinetic energy:

    KE = 0.5 * m * v**2

Available kinetic energy during deceleration:

    Delta_KE = KE_initial - KE_final

Estimated recovered electrical energy:

    E_electrical = Delta_KE * eta_total

The total recovery efficiency represents the combined effect of the
relevant mechanical, motor, inverter, and electrical charging losses.

IMPORTANT LIMITATIONS
---------------------
This program is a mathematical simulation, not a braking controller.

It does not model all vehicle dynamics, tyre-road constraints, motor
maps, battery charge limits, or detailed power-electronic behaviour.

Results depend on the assumptions and parameters supplied.
"""
import csv
import math
from pathlib import Path


# ============================================================
# SECTION 1: DEFAULT PROJECT PARAMETERS
# ============================================================

# Hypothetical vehicle mass, including occupants and payload.
DEFAULT_VEHICLE_MASS_KG = 1200.0

# Example initial vehicle speed in metres per second.
DEFAULT_INITIAL_SPEED_MPS = 15.0

# Example final vehicle speed after deceleration.
DEFAULT_FINAL_SPEED_MPS = 0.0

# Illustrative overall energy recovery efficiency.
# This is an assumption, not a universal EV specification.
DEFAULT_RECOVERY_EFFICIENCY = 0.70

# Fraction of translational kinetic energy used as a simplified
# allowance for rotating components.
# Zero disables this approximation.
DEFAULT_ROTATIONAL_ENERGY_FACTOR = 0.0

# Approximate gravitational acceleration, in m/s².
GRAVITY_MPS2 = 9.80665

# Conversion constants.
JOULES_PER_WH = 3600.0
JOULES_PER_KWH = 3_600_000.0
MPS_PER_KMH = 1.0 / 3.6


# ============================================================
# SECTION 2: INPUT VALIDATION
# ============================================================

def validate_finite_number(value, name):
    """
    Ensure a supplied value is a finite numerical quantity.

    Reject strings, NaN, and infinity to prevent invalid calculations.
    """

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a numerical value.")

    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")

    return float(value)


def validate_non_negative(value, name):
    """
    Validate quantities that cannot be negative in this model.
    """

    value = validate_finite_number(value, name)

    if value < 0:
        raise ValueError(f"{name} cannot be negative.")

    return value


def validate_positive(value, name):
    """
    Validate quantities that must be greater than zero.
    """

    value = validate_non_negative(value, name)

    if value == 0:
        raise ValueError(f"{name} must be greater than zero.")

    return value


def validate_efficiency(efficiency, name="efficiency"):
    """
    Validate an efficiency expressed as a fraction from 0 to 1.

    Example:
        0.70 represents 70% efficiency.
    """

    efficiency = validate_non_negative(efficiency, name)

    if efficiency > 1.0:
        raise ValueError(
            f"{name} must be between 0 and 1."
        )

    return efficiency


# ============================================================
# SECTION 3: UNIT CONVERSION FUNCTIONS
# ============================================================

def kmh_to_mps(speed_kmh):
    """
    Convert speed from kilometres per hour to metres per second.

    Formula:
        speed_mps = speed_kmh / 3.6
    """

    speed_kmh = validate_non_negative(speed_kmh, "speed_kmh")

    return speed_kmh / 3.6


def mps_to_kmh(speed_mps):
    """
    Convert speed from metres per second to kilometres per hour.
    """

    speed_mps = validate_non_negative(speed_mps, "speed_mps")

    return speed_mps * 3.6


def joules_to_wh(energy_j):
    """
    Convert energy from joules to watt-hours.
    """

    energy_j = validate_non_negative(energy_j, "energy_j")

    return energy_j / JOULES_PER_WH


def joules_to_kwh(energy_j):
    """
    Convert energy from joules to kilowatt-hours.
    """

    energy_j = validate_non_negative(energy_j, "energy_j")

    return energy_j / JOULES_PER_KWH


def wh_to_joules(energy_wh):
    """
    Convert energy from watt-hours to joules.
    """

    energy_wh = validate_non_negative(energy_wh, "energy_wh")

    return energy_wh * JOULES_PER_WH


# ============================================================
# SECTION 4: TRANSLATIONAL KINETIC ENERGY
# ============================================================

def calculate_kinetic_energy(
    vehicle_mass_kg,
    speed_mps,
):
    """
    Calculate the translational kinetic energy of a moving vehicle.

    Formula:
        KE = 0.5 * m * v**2

    Parameters:
        vehicle_mass_kg:
            Total moving vehicle mass, in kilograms.

        speed_mps:
            Vehicle speed, in metres per second.

    Returns:
        Kinetic energy in joules.

    Notes:
        This function calculates translational kinetic energy only.
        Rotational energy is handled separately.
    """

    # Validate the vehicle mass.
    mass = validate_positive(
        vehicle_mass_kg,
        "vehicle_mass_kg",
    )

    # Validate the speed.
    speed = validate_non_negative(
        speed_mps,
        "speed_mps",
    )

    # Apply the classical kinetic energy equation.
    kinetic_energy_j = 0.5 * mass * speed**2

    return kinetic_energy_j


# ============================================================
# SECTION 5: ROTATIONAL KINETIC ENERGY APPROXIMATION
# ============================================================

def calculate_effective_kinetic_energy(
    vehicle_mass_kg,
    speed_mps,
    rotational_energy_factor=DEFAULT_ROTATIONAL_ENERGY_FACTOR,
):
    """
    Calculate an approximate total kinetic energy including
    a simplified allowance for rotating vehicle components.

    Formula:
        Effective KE = Translational KE * (1 + factor)

    Parameters:
        rotational_energy_factor:
            A non-negative dimensionless modelling assumption.

            A value of 0.0 disables the rotational correction.
            A value of 0.05 adds 5% to translational kinetic energy.

    Returns:
        Effective kinetic energy estimate in joules.

    Limitations:
        This is a simplified approximation, not a substitute for
        calculating the inertia and angular velocity of each component.
    """

    # Validate the rotational correction parameter.
    factor = validate_non_negative(
        rotational_energy_factor,
        "rotational_energy_factor",
    )

    # Calculate the translational contribution.
    translational_energy = calculate_kinetic_energy(
        vehicle_mass_kg,
        speed_mps,
    )

    # Add the assumed rotational contribution.
    effective_energy = translational_energy * (1.0 + factor)

    return effective_energy


# ============================================================
# SECTION 6: ENERGY CHANGE DURING SPEED TRANSITIONS
# ============================================================

def calculate_energy_change(
    vehicle_mass_kg,
    initial_speed_mps,
    final_speed_mps,
    rotational_energy_factor=DEFAULT_ROTATIONAL_ENERGY_FACTOR,
):
    """
    Calculate the signed kinetic energy change between two speeds.

    Formula:
        Delta KE = KE_initial - KE_final

    Interpretation:
        Positive result:
            Kinetic energy decreases. Energy is available to be
            dissipated or potentially recovered.

        Zero result:
            No kinetic energy change in this simplified model.

        Negative result:
            Kinetic energy increases. The vehicle has accelerated,
            so this is not a regenerative braking event.

    Returns:
        Signed energy change in joules.

    Important:
        A positive energy change is only the available mechanical
        energy difference. It is not the recovered electrical energy.
    """

    # Calculate the initial effective kinetic energy.
    initial_energy = calculate_effective_kinetic_energy(
        vehicle_mass_kg,
        initial_speed_mps,
        rotational_energy_factor,
    )

    # Calculate the final effective kinetic energy.
    final_energy = calculate_effective_kinetic_energy(
        vehicle_mass_kg,
        final_speed_mps,
        rotational_energy_factor,
    )

    # Positive means kinetic energy has decreased.
    energy_change_j = initial_energy - final_energy

    return energy_change_j


def calculate_available_braking_energy(
    vehicle_mass_kg,
    initial_speed_mps,
    final_speed_mps,
    rotational_energy_factor=DEFAULT_ROTATIONAL_ENERGY_FACTOR,
):
    """
    Calculate the non-negative kinetic energy decrease available
    during a speed reduction.

    If the vehicle accelerates, the available braking energy is zero.

    Returns:
        Available mechanical energy in joules.
    """

    # Obtain the signed kinetic energy change.
    energy_change_j = calculate_energy_change(
        vehicle_mass_kg,
        initial_speed_mps,
        final_speed_mps,
        rotational_energy_factor,
    )

    # Regenerative recovery is only considered for energy decreases.
    return max(0.0, energy_change_j)


# ============================================================
# SECTION 7: REGENERATIVE ENERGY RECOVERY
# ============================================================

def estimate_recovered_energy(
    available_energy_j,
    recovery_efficiency=DEFAULT_RECOVERY_EFFICIENCY,
):
    """
    Estimate electrical energy recovered from available mechanical
    energy during a braking event.

    Formula:
        E_recovered = E_available * efficiency

    Parameters:
        available_energy_j:
            Available mechanical energy in joules.

        recovery_efficiency:
            Overall assumed conversion and recovery efficiency.

    Returns:
        Estimated recovered electrical energy in joules.

    This is a simplified lumped-efficiency model. Actual recovery
    depends on motor operation, power electronics, battery acceptance,
    vehicle speed, braking demand, and other constraints.
    """

    # Validate the available mechanical energy.
    available_energy = validate_non_negative(
        available_energy_j,
        "available_energy_j",
    )

    # Validate the overall recovery efficiency.
    efficiency = validate_efficiency(
        recovery_efficiency,
        "recovery_efficiency",
    )

    # Calculate the estimated electrical energy recovered.
    recovered_energy_j = available_energy * efficiency

    return recovered_energy_j


def estimate_recovery_losses(
    available_energy_j,
    recovered_energy_j,
):
    """
    Estimate the energy not returned as recovered electrical energy.

    Formula:
        Losses = Available energy - Recovered electrical energy

    The result is an aggregate difference for this simplified model.
    It does not identify where each loss occurs.
    """

    available = validate_non_negative(
        available_energy_j,
        "available_energy_j",
    )

    recovered = validate_non_negative(
        recovered_energy_j,
        "recovered_energy_j",
    )

    # Recovered energy cannot exceed the available energy here.
    if recovered > available + 1e-9:
        raise ValueError(
            "Recovered energy cannot exceed available energy."
        )

    # Remove any insignificant floating-point overshoot.
    recovered = min(recovered, available)

    return available - recovered


# ============================================================
# SECTION 8: COMPLETE BRAKING EVENT ANALYSIS
# ============================================================

def analyse_braking_event(
    vehicle_mass_kg,
    initial_speed_mps,
    final_speed_mps,
    recovery_efficiency=DEFAULT_RECOVERY_EFFICIENCY,
    rotational_energy_factor=DEFAULT_ROTATIONAL_ENERGY_FACTOR,
):
    """
    Analyse a single theoretical regenerative braking event.

    Returns a dictionary containing:
        Initial and final kinetic energy.
        Signed kinetic energy change.
        Available mechanical energy.
        Estimated recovered electrical energy.
        Estimated aggregate recovery losses.
        Recovery efficiency.
        Energy quantities in J, Wh, and kWh.
    """

    # Validate the overall recovery efficiency.
    efficiency = validate_efficiency(
        recovery_efficiency,
        "recovery_efficiency",
    )

    # Calculate the initial kinetic energy.
    initial_energy_j = calculate_effective_kinetic_energy(
        vehicle_mass_kg,
        initial_speed_mps,
        rotational_energy_factor,
    )

    # Calculate the final kinetic energy.
    final_energy_j = calculate_effective_kinetic_energy(
        vehicle_mass_kg,
        final_speed_mps,
        rotational_energy_factor,
    )

    # Calculate the signed kinetic energy change.
    signed_change_j = initial_energy_j - final_energy_j

    # Only a decrease in kinetic energy can provide braking energy.
    available_energy_j = max(0.0, signed_change_j)

    # Estimate electrical energy returned to storage.
    recovered_energy_j = estimate_recovered_energy(
        available_energy_j,
        efficiency,
    )

    # Calculate the aggregate difference.
    losses_j = estimate_recovery_losses(
        available_energy_j,
        recovered_energy_j,
    )

    # Describe the event without implying that recovery is guaranteed.
    if signed_change_j > 0:
        event_type = "deceleration"
    elif signed_change_j < 0:
        event_type = "acceleration"
    else:
        event_type = "constant_speed"

    # Assemble the full result.
    return {
        "event_type": event_type,
        "vehicle_mass_kg": float(vehicle_mass_kg),
        "initial_speed_mps": float(initial_speed_mps),
        "final_speed_mps": float(final_speed_mps),
        "initial_speed_kmh": mps_to_kmh(initial_speed_mps),
        "final_speed_kmh": mps_to_kmh(final_speed_mps),
        "initial_kinetic_energy_j": initial_energy_j,
        "final_kinetic_energy_j": final_energy_j,
        "signed_energy_change_j": signed_change_j,
        "available_mechanical_energy_j": available_energy_j,
        "recovered_electrical_energy_j": recovered_energy_j,
        "aggregate_recovery_losses_j": losses_j,
        "recovery_efficiency": efficiency,
        "rotational_energy_factor": float(
            rotational_energy_factor
        ),
        "initial_kinetic_energy_wh": joules_to_wh(
            initial_energy_j
        ),
        "final_kinetic_energy_wh": joules_to_wh(
            final_energy_j
        ),
        "available_mechanical_energy_wh": joules_to_wh(
            available_energy_j
        ),
        "recovered_electrical_energy_wh": joules_to_wh(
            recovered_energy_j
        ),
        "aggregate_recovery_losses_wh": joules_to_wh(
            losses_j
        ),
        "recovered_electrical_energy_kwh": joules_to_kwh(
            recovered_energy_j
        ),
    }


# ============================================================
# SECTION 9: BRAKING POWER ESTIMATION
# ============================================================

def estimate_braking_power(
    available_energy_j,
    braking_time_s,
    recovery_efficiency=DEFAULT_RECOVERY_EFFICIENCY,
):
    """
    Estimate average mechanical and electrical power during
    a defined braking interval.

    Formulas:
        Average mechanical power = available energy / time

        Average electrical recovery power =
            recovered electrical energy / time

    Returns:
        A dictionary of average power estimates in watts and kW.

    These are interval averages, not peak power predictions.
    """

    # Validate the energy, interval, and efficiency.
    energy = validate_non_negative(
        available_energy_j,
        "available_energy_j",
    )
    duration = validate_positive(
        braking_time_s,
        "braking_time_s",
    )
    efficiency = validate_efficiency(
        recovery_efficiency,
        "recovery_efficiency",
    )

    # Calculate the average mechanical power associated with
    # the kinetic energy decrease.
    average_mechanical_power_w = energy / duration

    # Estimate the electrical energy recovered.
    recovered_energy_j = estimate_recovered_energy(
        energy,
        efficiency,
    )

    # Calculate average recovered electrical power.
    average_electrical_power_w = recovered_energy_j / duration

    # Calculate the difference between these average powers.
    average_loss_power_w = (
        average_mechanical_power_w
        - average_electrical_power_w
    )

    return {
        "braking_time_s": duration,
        "average_mechanical_power_w": average_mechanical_power_w,
        "average_mechanical_power_kw": (
            average_mechanical_power_w / 1000.0
        ),
        "average_electrical_power_w": average_electrical_power_w,
        "average_electrical_power_kw": (
            average_electrical_power_w / 1000.0
        ),
        "average_loss_power_w": average_loss_power_w,
    }


# ============================================================
# SECTION 10: DISTANCE AND DECELERATION ESTIMATES
# ============================================================

def estimate_constant_deceleration(
    initial_speed_mps,
    final_speed_mps,
    braking_time_s,
):
    """
    Estimate average signed acceleration for a speed transition.

    Formula:
        a = (v_final - v_initial) / time

    Negative acceleration indicates deceleration in the chosen
    forward direction.
    """

    initial_speed = validate_non_negative(
        initial_speed_mps,
        "initial_speed_mps",
    )
    final_speed = validate_non_negative(
        final_speed_mps,
        "final_speed_mps",
    )
    duration = validate_positive(
        braking_time_s,
        "braking_time_s",
    )

    # Calculate the average acceleration.
    acceleration_mps2 = (
        final_speed - initial_speed
    ) / duration

    return acceleration_mps2


def estimate_constant_deceleration_distance(
    initial_speed_mps,
    final_speed_mps,
    braking_time_s,
):
    """
    Estimate distance during a speed transition assuming constant
    acceleration or deceleration.

    Formula:
        distance = average speed * time

        average speed = (v_initial + v_final) / 2

    This is a simplified kinematic estimate, not a braking safety
    calculation or a substitute for road-vehicle dynamics.
    """

    initial_speed = validate_non_negative(
        initial_speed_mps,
        "initial_speed_mps",
    )
    final_speed = validate_non_negative(
        final_speed_mps,
        "final_speed_mps",
    )
    duration = validate_positive(
        braking_time_s,
        "braking_time_s",
    )

    # Calculate average speed for constant acceleration.
    average_speed = (initial_speed + final_speed) / 2.0

    # Calculate the estimated distance travelled.
    distance_m = average_speed * duration

    return distance_m


# ============================================================
# SECTION 11: TIME-SERIES REGENERATIVE SIMULATION
# ============================================================

def simulate_regenerative_cycle(
    vehicle_mass_kg,
    time_seconds,
    speed_mps,
    recovery_efficiency=DEFAULT_RECOVERY_EFFICIENCY,
    rotational_energy_factor=DEFAULT_ROTATIONAL_ENERGY_FACTOR,
):
    """
    Simulate energy recovery from a sequence of speed samples.

    Inputs:
        time_seconds:
            Increasing timestamps in seconds.

        speed_mps:
            Corresponding non-negative speeds in m/s.

    Processing:
        Each consecutive pair of samples defines one interval.

        A positive kinetic energy decrease is treated as potentially
        available for regenerative recovery.

        An increase in kinetic energy does not produce a regenerative
        energy credit.

    Returns:
        Interval records and cumulative energy totals.

    Limitations:
        This model estimates the energy associated with speed changes.
        It does not simulate a complete motor controller, road loads,
        brake-force allocation, or battery charge acceptance.
    """

    # Validate the vehicle mass and overall efficiency.
    mass = validate_positive(
        vehicle_mass_kg,
        "vehicle_mass_kg",
    )
    efficiency = validate_efficiency(
        recovery_efficiency,
        "recovery_efficiency",
    )
    rotational_factor = validate_non_negative(
        rotational_energy_factor,
        "rotational_energy_factor",
    )

    # Both arrays must contain corresponding samples.
    if len(time_seconds) != len(speed_mps):
        raise ValueError(
            "Time and speed arrays must have equal lengths."
        )

    # At least two samples are needed for interval calculations.
    if len(time_seconds) < 2:
        raise ValueError(
            "At least two time and speed samples are required."
        )

    # Validate every timestamp.
    times = [
        validate_non_negative(value, "time_seconds")
        for value in time_seconds
    ]

    # Validate every speed sample.
    speeds = [
        validate_non_negative(value, "speed_mps")
        for value in speed_mps
    ]

    # Ensure that timestamps are strictly increasing.
    for index in range(len(times) - 1):
        if times[index + 1] <= times[index]:
            raise ValueError(
                "Timestamps must be strictly increasing."
            )

    # Prepare the interval records.
    interval_results = []

    # Initialise cumulative energy counters.
    cumulative_available_j = 0.0
    cumulative_recovered_j = 0.0
    cumulative_losses_j = 0.0

    # Process each consecutive pair of samples.
    for index in range(len(times) - 1):

        # Read the current interval's starting and ending values.
        start_time = times[index]
        end_time = times[index + 1]
        start_speed = speeds[index]
        end_speed = speeds[index + 1]

        # Calculate elapsed time for this interval.
        duration_s = end_time - start_time

        # Analyse the change in kinetic energy.
        event = analyse_braking_event(
            vehicle_mass_kg=mass,
            initial_speed_mps=start_speed,
            final_speed_mps=end_speed,
            recovery_efficiency=efficiency,
            rotational_energy_factor=rotational_factor,
        )

        # Obtain the available and recovered energy estimates.
        available_j = event["available_mechanical_energy_j"]
        recovered_j = event["recovered_electrical_energy_j"]
        losses_j = event["aggregate_recovery_losses_j"]

        # Calculate interval-average power values.
        mechanical_power_w = available_j / duration_s
        electrical_power_w = recovered_j / duration_s

        # Accumulate the energy totals.
        cumulative_available_j += available_j
        cumulative_recovered_j += recovered_j
        cumulative_losses_j += losses_j

        # Store a record of the current interval.
        interval_results.append({
            "start_time_s": start_time,
            "end_time_s": end_time,
            "duration_s": duration_s,
            "initial_speed_mps": start_speed,
            "final_speed_mps": end_speed,
            "initial_speed_kmh": mps_to_kmh(start_speed),
            "final_speed_kmh": mps_to_kmh(end_speed),
            "event_type": event["event_type"],
            "signed_energy_change_j": (
                event["signed_energy_change_j"]
            ),
            "available_mechanical_energy_j": available_j,
            "recovered_electrical_energy_j": recovered_j,
            "aggregate_recovery_losses_j": losses_j,
            "average_mechanical_power_w": mechanical_power_w,
            "average_electrical_power_w": electrical_power_w,
            "cumulative_available_energy_j": cumulative_available_j,
            "cumulative_recovered_energy_j": cumulative_recovered_j,
            "cumulative_losses_j": cumulative_losses_j,
        })

    # Count intervals with a positive kinetic energy decrease.
    braking_intervals = sum(
        1 for record in interval_results
        if record["event_type"] == "deceleration"
    )

    # Calculate the total duration represented by the samples.
    total_duration_s = times[-1] - times[0]

    # Return the simulation data and summary values.
    return {
        "vehicle_mass_kg": mass,
        "recovery_efficiency": efficiency,
        "rotational_energy_factor": rotational_factor,
        "start_time_s": times[0],
        "end_time_s": times[-1],
        "total_duration_s": total_duration_s,
        "number_of_intervals": len(interval_results),
        "number_of_braking_intervals": braking_intervals,
        "interval_results": interval_results,
        "total_available_mechanical_energy_j": (
            cumulative_available_j
        ),
        "total_recovered_electrical_energy_j": (
            cumulative_recovered_j
        ),
        "total_aggregate_losses_j": cumulative_losses_j,
        "total_available_mechanical_energy_wh": (
            joules_to_wh(cumulative_available_j)
        ),
        "total_recovered_electrical_energy_wh": (
            joules_to_wh(cumulative_recovered_j)
        ),
        "total_recovered_electrical_energy_kwh": (
            joules_to_kwh(cumulative_recovered_j)
        ),
        "total_aggregate_losses_wh": (
            joules_to_wh(cumulative_losses_j)
        ),
    }


# ============================================================
# SECTION 12: ANALYSING MULTIPLE BRAKING EVENTS
# ============================================================

def analyse_multiple_braking_events(
    vehicle_mass_kg,
    braking_events,
    recovery_efficiency=DEFAULT_RECOVERY_EFFICIENCY,
    rotational_energy_factor=DEFAULT_ROTATIONAL_ENERGY_FACTOR,
):
    """
    Analyse a list of independent braking events.

    Each event must be a dictionary containing:
        initial_speed_mps
        final_speed_mps

    An optional event identifier may also be supplied.

    Returns:
        Individual event results and cumulative totals.

    Important:
        Events are treated as separate speed transitions. This function
        does not infer the driving route or add energy between events.
    """

    # Validate the shared vehicle parameters.
    mass = validate_positive(
        vehicle_mass_kg,
        "vehicle_mass_kg",
    )
    efficiency = validate_efficiency(
        recovery_efficiency,
        "recovery_efficiency",
    )
    rotational_factor = validate_non_negative(
        rotational_energy_factor,
        "rotational_energy_factor",
    )

    # Prepare event records and aggregate counters.
    event_results = []
    total_available_j = 0.0
    total_recovered_j = 0.0
    total_losses_j = 0.0

    # Process each independent event.
    for index, event in enumerate(braking_events):

        # Check that each event contains the required information.
        if "initial_speed_mps" not in event:
            raise KeyError(
                f"Event {index} lacks initial_speed_mps."
            )

        if "final_speed_mps" not in event:
            raise KeyError(
                f"Event {index} lacks final_speed_mps."
            )

        # Analyse the current event.
        result = analyse_braking_event(
            vehicle_mass_kg=mass,
            initial_speed_mps=event["initial_speed_mps"],
            final_speed_mps=event["final_speed_mps"],
            recovery_efficiency=efficiency,
            rotational_energy_factor=rotational_factor,
        )

        # Attach an identifier for traceability.
        result["event_id"] = event.get(
            "event_id",
            f"event_{index + 1}",
        )

        # Accumulate the event energy estimates.
        total_available_j += (
            result["available_mechanical_energy_j"]
        )
        total_recovered_j += (
            result["recovered_electrical_energy_j"]
        )
        total_losses_j += (
            result["aggregate_recovery_losses_j"]
        )

        event_results.append(result)

    # Return the detailed records and aggregate totals.
    return {
        "vehicle_mass_kg": mass,
        "recovery_efficiency": efficiency,
        "number_of_events": len(event_results),
        "events": event_results,
        "total_available_mechanical_energy_j": total_available_j,
        "total_recovered_electrical_energy_j": total_recovered_j,
        "total_aggregate_losses_j": total_losses_j,
        "total_available_mechanical_energy_wh": (
            joules_to_wh(total_available_j)
        ),
        "total_recovered_electrical_energy_wh": (
            joules_to_wh(total_recovered_j)
        ),
        "total_recovered_electrical_energy_kwh": (
            joules_to_kwh(total_recovered_j)
        ),
        "total_aggregate_losses_wh": (
            joules_to_wh(total_losses_j)
        ),
    }


# ============================================================
# SECTION 13: CSV EXPORT FOR A SINGLE EVENT
# ============================================================

def export_event_to_csv(
    event_result,
    filename="data/regenerative_event.csv",
):
    """
    Export a single braking-event report to CSV.

    Each row contains one measurement or calculated metric.
    """

    # Resolve the destination path.
    output_path = Path(filename)

    # Create the destination folder if required.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Select the event fields to export.
    fields = [
        "event_type",
        "vehicle_mass_kg",
        "initial_speed_mps",
        "final_speed_mps",
        "initial_speed_kmh",
        "final_speed_kmh",
        "initial_kinetic_energy_j",
        "final_kinetic_energy_j",
        "signed_energy_change_j",
        "available_mechanical_energy_j",
        "recovered_electrical_energy_j",
        "aggregate_recovery_losses_j",
        "recovery_efficiency",
        "available_mechanical_energy_wh",
        "recovered_electrical_energy_wh",
        "aggregate_recovery_losses_wh",
        "recovered_electrical_energy_kwh",
    ]

    # Write the event summary as a one-row CSV.
    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerow(event_result)

    return output_path


# ============================================================
# SECTION 14: CSV EXPORT FOR TIME-SERIES RESULTS
# ============================================================

def export_cycle_to_csv(
    cycle_results,
    filename="data/regenerative_cycle.csv",
):
    """
    Export interval-by-interval regenerative simulation data.

    Each row represents one interval between consecutive speed samples.
    """

    # Obtain the individual interval records.
    records = cycle_results["interval_results"]

    # Resolve the destination path and create parent folders.
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Do not create a misleading empty data table.
    if not records:
        raise ValueError(
            "The simulation contains no interval results."
        )

    # Use the first record to determine the CSV columns.
    fieldnames = list(records[0].keys())

    # Write the time-series records.
    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(records)

    return output_path


# ============================================================
# SECTION 15: VISUALISING A SINGLE BRAKING EVENT
# ============================================================

def plot_braking_event(
    event_result,
    save_plot=False,
):
    """
    Plot the energy distribution for a single braking event.

    Matplotlib is imported only when plotting is requested.
    """

    try:
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise ImportError(
            "Install Matplotlib with: python -m pip install matplotlib"
        ) from error

    # Prepare the quantities for the energy comparison.
    labels = [
        "Initial kinetic\nenergy",
        "Final kinetic\nenergy",
        "Available mechanical\nenergy",
        "Recovered electrical\nenergy",
        "Aggregate recovery\nlosses",
    ]

    values = [
        joules_to_wh(event_result["initial_kinetic_energy_j"]),
        joules_to_wh(event_result["final_kinetic_energy_j"]),
        event_result["available_mechanical_energy_wh"],
        event_result["recovered_electrical_energy_wh"],
        event_result["aggregate_recovery_losses_wh"],
    ]

    # Create a chart showing the energy quantities.
    figure, axis = plt.subplots(figsize=(11, 6))

    # Draw the comparison bars.
    axis.bar(labels, values)

    # Label the axes and chart.
    axis.set_ylabel("Energy (Wh)")
    axis.set_title("Fluxxwave — Regenerative Braking Energy Analysis")
    axis.grid(axis="y", alpha=0.3)

    # Improve readability of category labels.
    figure.tight_layout()

    # Optionally save a high-resolution image.
    if save_plot:
        figure.savefig(
            "regenerative_event.png",
            dpi=300,
            bbox_inches="tight",
        )

    # Display the chart.
    plt.show()


# ============================================================
# SECTION 16: VISUALISING A TIME-SERIES SIMULATION
# ============================================================

def plot_regenerative_cycle(
    cycle_results,
    save_plot=False,
):
    """
    Plot vehicle speed, cumulative recovered energy, and
    average recovered electrical power across simulation intervals.
    """

    try:
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise ImportError(
            "Install Matplotlib with: python -m pip install matplotlib"
        ) from error

    # Extract the simulation intervals.
    records = cycle_results["interval_results"]

    if not records:
        raise ValueError("No time-series data is available to plot.")

    # Build arrays for the graphs.
    interval_times = [
        row["end_time_s"] for row in records
    ]

    final_speeds = [
        row["final_speed_kmh"] for row in records
    ]

    cumulative_recovered_wh = [
        joules_to_wh(row["cumulative_recovered_energy_j"])
        for row in records
    ]

    recovered_power_w = [
        row["average_electrical_power_w"]
        for row in records
    ]

    # Create three vertically stacked graphs.
    figure, axes = plt.subplots(
        3,
        1,
        figsize=(11, 10),
        sharex=True,
    )

    # Graph 1: speed across the simulation.
    axes[0].plot(interval_times, final_speeds)
    axes[0].set_ylabel("Speed (km/h)")
    axes[0].set_title("Vehicle Speed")
    axes[0].grid(True)

    # Graph 2: accumulated electrical energy recovery.
    axes[1].plot(interval_times, cumulative_recovered_wh)
    axes[1].set_ylabel("Recovered energy (Wh)")
    axes[1].set_title("Cumulative Recovered Electrical Energy")
    axes[1].grid(True)

    # Graph 3: average recovered power in each interval.
    axes[2].plot(interval_times, recovered_power_w)
    axes[2].set_ylabel("Average power (W)")
    axes[2].set_xlabel("Time (s)")
    axes[2].set_title("Interval-Average Recovered Electrical Power")
    axes[2].grid(True)

    # Prevent the graph labels from overlapping.
    figure.tight_layout()

    # Save the figure if requested.
    if save_plot:
        figure.savefig(
            "regenerative_cycle.png",
            dpi=300,
            bbox_inches="tight",
        )

    # Display the plots.
    plt.show()


# ============================================================
# SECTION 17: PRINTING A SINGLE-EVENT REPORT
# ============================================================

def print_event_report(event_result):
    """
    Display the results of one braking event in a readable format.
    """

    print("\n" + "=" * 66)
    print("       FLUXXWAVE REGENERATIVE ENERGY REPORT")
    print("=" * 66)

    # Display the event classification.
    print(f"Event type:                  {event_result['event_type']}")

    # Display vehicle parameters.
    print(
        f"Vehicle mass:                "
        f"{event_result['vehicle_mass_kg']:.2f} kg"
    )
    print(
        f"Initial speed:               "
        f"{event_result['initial_speed_kmh']:.2f} km/h"
    )
    print(
        f"Final speed:                 "
        f"{event_result['final_speed_kmh']:.2f} km/h"
    )

    print("-" * 66)

    # Display initial and final kinetic energy.
    print(
        f"Initial kinetic energy:      "
        f"{event_result['initial_kinetic_energy_j']:.2f} J"
    )
    print(
        f"Final kinetic energy:        "
        f"{event_result['final_kinetic_energy_j']:.2f} J"
    )

    # Display the energy available for recovery.
    print(
        f"Signed energy change:        "
        f"{event_result['signed_energy_change_j']:.2f} J"
    )
    print(
        f"Available mechanical energy: "
        f"{event_result['available_mechanical_energy_j']:.2f} J"
    )
    print(
        f"Available mechanical energy: "
        f"{event_result['available_mechanical_energy_wh']:.4f} Wh"
    )

    print("-" * 66)

    # Display the recovery assumptions.
    print(
        f"Assumed recovery efficiency: "
        f"{event_result['recovery_efficiency'] * 100:.1f}%"
    )

    # Display the electrical recovery estimate.
    print(
        f"Recovered electrical energy: "
        f"{event_result['recovered_electrical_energy_j']:.2f} J"
    )
    print(
        f"Recovered electrical energy: "
        f"{event_result['recovered_electrical_energy_wh']:.4f} Wh"
    )
    print(
        f"Recovered electrical energy: "
        f"{event_result['recovered_electrical_energy_kwh']:.8f} kWh"
    )

    # Display the aggregate loss estimate.
    print(
        f"Aggregate recovery losses:   "
        f"{event_result['aggregate_recovery_losses_j']:.2f} J"
    )
    print(
        f"Aggregate recovery losses:   "
        f"{event_result['aggregate_recovery_losses_wh']:.4f} Wh"
    )

    print("=" * 66)
    print("Results are mathematical estimates, not hardware measurements.")
    print("=" * 66 + "\n")


# ============================================================
# SECTION 18: PRINTING A TIME-SERIES SUMMARY
# ============================================================

def print_cycle_report(cycle_results):
    """
    Print the overall results of a speed-profile simulation.
    """

    print("\n" + "=" * 66)
    print("       FLUXXWAVE REGENERATIVE CYCLE SUMMARY")
    print("=" * 66)

    # Display the vehicle and simulation parameters.
    print(
        f"Vehicle mass:                "
        f"{cycle_results['vehicle_mass_kg']:.2f} kg"
    )
    print(
        f"Recovery efficiency:         "
        f"{cycle_results['recovery_efficiency'] * 100:.1f}%"
    )
    print(
        f"Simulation duration:         "
        f"{cycle_results['total_duration_s']:.2f} s"
    )
    print(
        f"Intervals processed:         "
        f"{cycle_results['number_of_intervals']}"
    )
    print(
        f"Deceleration intervals:      "
        f"{cycle_results['number_of_braking_intervals']}"
    )

    print("-" * 66)

    # Display total energy estimates.
    print(
        f"Available mechanical energy: "
        f"{cycle_results['total_available_mechanical_energy_wh']:.4f} Wh"
    )
    print(
        f"Recovered electrical energy: "
        f"{cycle_results['total_recovered_electrical_energy_wh']:.4f} Wh"
    )
    print(
        f"Recovered electrical energy: "
        f"{cycle_results['total_recovered_electrical_energy_kwh']:.8f} kWh"
    )
    print(
        f"Aggregate recovery losses:   "
        f"{cycle_results['total_aggregate_losses_wh']:.4f} Wh"
    )

    print("=" * 66)
    print("These totals depend on the supplied speed profile and assumptions.")
    print("=" * 66 + "\n")


# ============================================================
# SECTION 19: EXAMPLE BRAKING EVENT
# ============================================================

def run_single_event_example():
    """
    Run a single example: a hypothetical vehicle slows from
    54 km/h to rest.

    The speeds are converted to m/s before the energy calculations.
    """

    # Define the hypothetical vehicle mass.
    vehicle_mass = DEFAULT_VEHICLE_MASS_KG

    # Define the initial and final speeds in km/h.
    initial_speed_kmh = 54.0
    final_speed_kmh = 0.0

    # Convert the speeds to the SI unit required by the equations.
    initial_speed_mps = kmh_to_mps(initial_speed_kmh)
    final_speed_mps = kmh_to_mps(final_speed_kmh)

    # Analyse the braking event using the assumed recovery efficiency.
    result = analyse_braking_event(
        vehicle_mass_kg=vehicle_mass,
        initial_speed_mps=initial_speed_mps,
        final_speed_mps=final_speed_mps,
        recovery_efficiency=0.70,
    )

    # Print the complete event report.
    print_event_report(result)

    # Estimate average power for an illustrative braking duration.
    # This is an assumed duration, not a braking recommendation.
    power_result = estimate_braking_power(
        available_energy_j=result["available_mechanical_energy_j"],
        braking_time_s=5.0,
        recovery_efficiency=0.70,
    )

    print("ILLUSTRATIVE AVERAGE POWER")
    print("-" * 40)
    print(
        f"Average mechanical power: "
        f"{power_result['average_mechanical_power_w']:.2f} W"
    )
    print(
        f"Average electrical power: "
        f"{power_result['average_electrical_power_w']:.2f} W"
    )

    # Export the event results for later analysis.
    csv_path = export_event_to_csv(
        result,
        "data/regenerative_event.csv",
    )
    print(f"\nEvent CSV saved to: {csv_path}")

    return result


# ============================================================
# SECTION 20: EXAMPLE SPEED-PROFILE SIMULATION
# ============================================================

def run_cycle_example():
    """
    Demonstrate recovery estimates from a hypothetical speed profile.

    The data below are illustrative simulation inputs, not recorded
    measurements from an actual vehicle.
    """

    # Define timestamps in seconds.
    times = [
        0, 5, 10, 15, 20, 25, 30
    ]

    # Define vehicle speeds in km/h.
    speeds_kmh = [
        54, 54, 45, 30, 15, 0, 0
    ]

    # Convert all speeds to m/s.
    speeds_mps = [
        kmh_to_mps(speed) for speed in speeds_kmh
    ]

    # Simulate the speed profile.
    results = simulate_regenerative_cycle(
        vehicle_mass_kg=DEFAULT_VEHICLE_MASS_KG,
        time_seconds=times,
        speed_mps=speeds_mps,
        recovery_efficiency=0.70,
    )

    # Print the cumulative energy summary.
    print_cycle_report(results)

    # Save the time-series results.
    csv_path = export_cycle_to_csv(
        results,
        "data/regenerative_cycle.csv",
    )
    print(f"Cycle CSV saved to: {csv_path}")

    return results


# ============================================================
# SECTION 21: PROGRAM ENTRY POINT
# ============================================================

def main():
    """
    Run the demonstration when this file is executed directly.

    The mathematical functions remain importable by other modules.
    """

    print("\nStarting Fluxxwave regenerative-energy simulation...")

    # Run the single-event example.
    single_event_results = run_single_event_example()

    # Run the speed-profile example.
    cycle_results = run_cycle_example()

    # Plot results only when Matplotlib is available.
    try:
        plot_braking_event(
            single_event_results,
            save_plot=True,
        )

        plot_regenerative_cycle(
            cycle_results,
            save_plot=True,
        )

        print("Graphs saved successfully.")

    except ImportError as error:
        print(f"\nPlotting unavailable: {error}")
        print("The numerical calculations and CSV exports are complete.")

    print("\nFluxxwave regenerative simulation finished.")


# Execute the examples only when the file is run directly.
if __name__ == "__main__":
    main()
