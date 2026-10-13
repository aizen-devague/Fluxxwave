
"""
FLUXXWAVE — BATTERY MODEL
=========================

Purpose:
    Simulate the state and behaviour of two independent batteries
    in the Fluxxwave electric vehicle concept.

Features:
    1. Battery A and Battery B can have different specifications.
    2. Track state of charge (SoC).
    3. Calculate stored and available energy.
    4. Simulate energy consumption and charging.
    5. Track nominal voltage and estimated terminal voltage.
    6. Track temperature and configurable operating limits.
    7. Check whether a battery is eligible for simulated use.
    8. Detect invalid states and simulated fault conditions.
    9. Export battery information for logging and analysis.
    10. Demonstrate both batteries operating independently.

IMPORTANT LIMITATIONS:
    This is a simplified mathematical simulation.

    The voltage model is illustrative and is not a real battery
    voltage-versus-SoC curve.

    The temperature model does not simulate electrochemical heating
    or cooling.

    The code does not communicate with a physical battery, replace
    a battery-management system (BMS), or implement safety hardware.
"""

from dataclasses import dataclass, field
from typing import Optional
import math


# ============================================================
# SECTION 1: DEFAULT CONFIGURATION
# ============================================================

# Default minimum permitted simulated state of charge.
DEFAULT_MIN_SOC = 0.0

# Default maximum permitted simulated state of charge.
DEFAULT_MAX_SOC = 100.0

# Example temperature limits for the software model, in °C.
# Replace these with limits justified by the chosen battery's data.
DEFAULT_MIN_TEMPERATURE_C = 0.0
DEFAULT_MAX_TEMPERATURE_C = 45.0

# Example minimum voltage allowed by the simplified model.
# These values are illustrative, not chemistry-specific limits.
DEFAULT_MIN_VOLTAGE_V = 0.0

# Numerical tolerance for floating-point comparisons.
NUMERICAL_TOLERANCE = 1e-9


# ============================================================
# SECTION 2: INPUT VALIDATION
# ============================================================

def validate_number(value, name):
    """
    Ensure that an input is a finite numerical value.

    Reject booleans, strings, NaN, and infinity.
    """

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a numerical value.")

    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite.")

    return float(value)


def validate_non_negative(value, name):
    """Reject negative numerical values."""

    value = validate_number(value, name)

    if value < 0:
        raise ValueError(f"{name} cannot be negative.")

    return value


def validate_positive(value, name):
    """Require a numerical value greater than zero."""

    value = validate_non_negative(value, name)

    if value == 0:
        raise ValueError(f"{name} must be greater than zero.")

    return value


def validate_percentage(value, name):
    """Validate a percentage between 0% and 100%."""

    value = validate_number(value, name)

    if not 0.0 <= value <= 100.0:
        raise ValueError(f"{name} must be between 0 and 100.")

    return value


# ============================================================
# SECTION 3: BATTERY DATA MODEL
# ============================================================

@dataclass
class Battery:
    """
    Represent one battery in the Fluxxwave simulation.

    Each instance maintains its own state. Battery A and Battery B
    do not automatically share charge or operating conditions.

    Capacity is specified in kWh, voltage in volts, temperature in
    degrees Celsius, and power in watts.
    """

    # A unique descriptive name, such as "Battery A".
    name: str

    # Nominal energy capacity in kilowatt-hours.
    capacity_kwh: float

    # Nominal voltage used by the simplified voltage model.
    nominal_voltage_v: float

    # Current simulated state of charge, expressed as a percentage.
    soc_percent: float = 100.0

    # Current simulated battery temperature.
    temperature_c: float = 25.0

    # Minimum permitted SoC for this model.
    min_soc_percent: float = DEFAULT_MIN_SOC

    # Maximum permitted SoC for this model.
    max_soc_percent: float = DEFAULT_MAX_SOC

    # Temperature limits for simulated operating eligibility.
    min_temperature_c: float = DEFAULT_MIN_TEMPERATURE_C
    max_temperature_c: float = DEFAULT_MAX_TEMPERATURE_C

    # Voltage limits for the illustrative terminal-voltage model.
    min_voltage_v: float = DEFAULT_MIN_VOLTAGE_V
    max_voltage_v: Optional[float] = None

    # Estimated discharge voltage at 0% SoC.
    # This is an illustrative parameter, not a real cell specification.
    voltage_at_zero_soc_v: Optional[float] = None

    # Optional maximum simulated discharge power.
    max_discharge_power_w: Optional[float] = None

    # Optional maximum simulated charging power.
    max_charge_power_w: Optional[float] = None

    # Fraction of input energy retained during simulated charging.
    # For example, 0.95 represents 95% charging efficiency.
    charge_efficiency: float = 0.95

    # Enable or disable the battery in the simulation.
    enabled: bool = True

    # Store fault descriptions for the current simulated state.
    faults: list = field(default_factory=list)

    # Track the number of simulated charge/discharge operations.
    operation_count: int = 0

    # Accumulate energy consumed from this battery, in kWh.
    total_energy_consumed_kwh: float = 0.0

    # Accumulate energy delivered into this battery, in kWh.
    total_energy_added_kwh: float = 0.0

    def __post_init__(self):
        """
        Validate initial settings after the object is created.
        """

        # A name is needed to distinguish the batteries.
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Battery name cannot be empty.")

        # Validate the basic electrical and storage parameters.
        self.capacity_kwh = validate_positive(
            self.capacity_kwh, "capacity_kwh"
        )

        self.nominal_voltage_v = validate_positive(
            self.nominal_voltage_v, "nominal_voltage_v"
        )

        self.soc_percent = validate_percentage(
            self.soc_percent, "soc_percent"
        )

        self.temperature_c = validate_number(
            self.temperature_c, "temperature_c"
        )

        # Validate SoC limits.
        self.min_soc_percent = validate_percentage(
            self.min_soc_percent, "min_soc_percent"
        )

        self.max_soc_percent = validate_percentage(
            self.max_soc_percent, "max_soc_percent"
        )

        if self.min_soc_percent >= self.max_soc_percent:
            raise ValueError(
                "Minimum SoC must be lower than maximum SoC."
            )

        if not (
            self.min_soc_percent
            <= self.soc_percent
            <= self.max_soc_percent
        ):
            raise ValueError(
                "Initial SoC must be within the configured limits."
            )

        # Validate temperature limits.
        self.min_temperature_c = validate_number(
            self.min_temperature_c, "min_temperature_c"
        )

        self.max_temperature_c = validate_number(
            self.max_temperature_c, "max_temperature_c"
        )

        if self.min_temperature_c >= self.max_temperature_c:
            raise ValueError(
                "Minimum temperature must be lower than maximum."
            )

        # Validate the illustrative voltage limits.
        self.min_voltage_v = validate_non_negative(
            self.min_voltage_v, "min_voltage_v"
        )

        if self.max_voltage_v is None:
            # Default to nominal voltage as the upper model limit.
            self.max_voltage_v = self.nominal_voltage_v

        self.max_voltage_v = validate_positive(
            self.max_voltage_v, "max_voltage_v"
        )

        if self.min_voltage_v >= self.max_voltage_v:
            raise ValueError(
                "Minimum voltage must be below maximum voltage."
            )

        # If no lower-end voltage is supplied, derive a simple default.
        if self.voltage_at_zero_soc_v is None:
            self.voltage_at_zero_soc_v = (
                self.nominal_voltage_v * 0.80
            )

        self.voltage_at_zero_soc_v = validate_non_negative(
            self.voltage_at_zero_soc_v,
            "voltage_at_zero_soc_v",
        )

        # Validate optional power limits.
        if self.max_discharge_power_w is not None:
            self.max_discharge_power_w = validate_positive(
                self.max_discharge_power_w,
                "max_discharge_power_w",
            )

        if self.max_charge_power_w is not None:
            self.max_charge_power_w = validate_positive(
                self.max_charge_power_w,
                "max_charge_power_w",
            )

        # Validate the charging efficiency.
        self.charge_efficiency = validate_percentage(
            self.charge_efficiency * 100.0,
            "charge_efficiency_fraction",
        ) / 100.0

        # Validate the accumulated energy counters.
        self.total_energy_consumed_kwh = validate_non_negative(
            self.total_energy_consumed_kwh,
            "total_energy_consumed_kwh",
        )

        self.total_energy_added_kwh = validate_non_negative(
            self.total_energy_added_kwh,
            "total_energy_added_kwh",
        )

        # Check the initial state against the model's operating limits.
        self.check_battery_status()

    # ========================================================
    # SECTION 4: STATE OF CHARGE AND STORED ENERGY
    # ========================================================

    def update_soc(self, new_soc_percent):
        """
        Set the simulated state of charge to a new value.

        This method represents an externally calculated or supplied
        SoC estimate. It does not calculate SoC from real sensor data.

        Returns:
            The updated SoC percentage.
        """

        # Validate the requested state of charge.
        new_soc = validate_percentage(
            new_soc_percent, "new_soc_percent"
        )

        # Prevent the model from moving outside its configured limits.
        if not (
            self.min_soc_percent
            <= new_soc
            <= self.max_soc_percent
        ):
            raise ValueError(
                f"{self.name}: requested SoC is outside "
                "the configured limits."
            )

        # Store the updated value.
        self.soc_percent = new_soc

        # Re-evaluate the operating state.
        self.check_battery_status()

        return self.soc_percent

    @property
    def stored_energy_kwh(self):
        """
        Estimate stored energy from capacity and SoC.

        Formula:
            Stored energy = capacity * SoC / 100

        This assumes a linear relationship between SoC and stored
        usable energy for the purposes of the simplified simulation.
        """

        return self.capacity_kwh * self.soc_percent / 100.0

    @property
    def stored_energy_wh(self):
        """Return estimated stored energy in watt-hours."""

        return self.stored_energy_kwh * 1000.0

    @property
    def minimum_energy_kwh(self):
        """Return the energy corresponding to minimum permitted SoC."""

        return (
            self.capacity_kwh
            * self.min_soc_percent
            / 100.0
        )

    @property
    def maximum_energy_kwh(self):
        """Return the energy corresponding to maximum permitted SoC."""

        return (
            self.capacity_kwh
            * self.max_soc_percent
            / 100.0
        )

    @property
    def available_energy_kwh(self):
        """
        Estimate energy available for consumption before reaching
        the configured minimum SoC.
        """

        return max(
            0.0,
            self.stored_energy_kwh - self.minimum_energy_kwh,
        )

    @property
    def available_energy_wh(self):
        """Return energy available for consumption in Wh."""

        return self.available_energy_kwh * 1000.0

    @property
    def remaining_charge_capacity_kwh(self):
        """Estimate additional stored energy before maximum SoC."""

        return max(
            0.0,
            self.maximum_energy_kwh - self.stored_energy_kwh,
        )

    @property
    def remaining_charge_capacity_wh(self):
        """Return remaining storage capacity in Wh."""

        return self.remaining_charge_capacity_kwh * 1000.0

    # ========================================================
    # SECTION 5: SIMPLIFIED VOLTAGE ESTIMATION
    # ========================================================

    @property
    def estimated_voltage_v(self):
        """
        Estimate voltage using a simple linear SoC relationship.

        Formula:
            V = V_zero + (V_nominal - V_zero) * SoC / 100

        This is only an illustrative software model. Actual battery
        voltage depends on chemistry, current, temperature, cell
        characteristics, and other factors.
        """

        # Calculate the voltage range represented by the model.
        voltage_range = (
            self.nominal_voltage_v
            - self.voltage_at_zero_soc_v
        )

        # Estimate voltage at the current simulated SoC.
        estimated_voltage = (
            self.voltage_at_zero_soc_v
            + voltage_range * self.soc_percent / 100.0
        )

        # Return the estimated voltage.
        return estimated_voltage

    @property
    def estimated_power_w(self):
        """
        Return an illustrative power estimate.

        This property reports zero because the battery model does
        not know the actual current or connected load. Power should
        be calculated from an explicit load model or measurements.
        """

        return 0.0

    # ========================================================
    # SECTION 6: CONSUMING ENERGY
    # ========================================================

    def consume_energy(self, energy_kwh, duration_s=None):
        """
        Simulate consuming energy from the battery.

        Parameters:
            energy_kwh:
                Requested energy drawn from the battery, in kWh.

            duration_s:
                Optional duration of the operation in seconds.

        Returns:
            A dictionary containing the requested energy, updated SoC,
            remaining energy, and operating status.

        The operation is rejected if it would exceed the configured
        minimum SoC or a supplied discharge-power limit.
        """

        # Validate the energy request.
        requested_energy = validate_non_negative(
            energy_kwh, "energy_kwh"
        )

        # Validate duration when supplied.
        if duration_s is not None:
            duration_s = validate_positive(
                duration_s, "duration_s"
            )

        # Check whether the battery is eligible for use.
        if not self.check_battery_status():
            raise RuntimeError(
                f"{self.name} is unavailable: "
                f"{', '.join(self.faults)}"
            )

        # Calculate the requested average power when duration is known.
        if duration_s is not None and duration_s > 0:
            requested_power_w = (
                requested_energy * 3_600_000.0 / duration_s
            )
        else:
            requested_power_w = None

        # Enforce the configured discharge-power limit.
        if (
            requested_power_w is not None
            and self.max_discharge_power_w is not None
            and requested_power_w
            > self.max_discharge_power_w + NUMERICAL_TOLERANCE
        ):
            raise ValueError(
                f"{self.name}: requested discharge power exceeds "
                "the configured simulation limit."
            )

        # Calculate the energy available above minimum SoC.
        available_energy = self.available_energy_kwh

        # Reject a request that would exceed the available energy.
        if requested_energy > available_energy + NUMERICAL_TOLERANCE:
            raise ValueError(
                f"{self.name}: insufficient available energy. "
                f"Available: {available_energy:.6f} kWh; "
                f"requested: {requested_energy:.6f} kWh."
            )

        # Prevent tiny floating-point errors from creating a negative state.
        requested_energy = min(
            requested_energy,
            available_energy,
        )

        # Calculate the corresponding SoC reduction.
        soc_reduction = (
            requested_energy / self.capacity_kwh * 100.0
        )

        # Update the simulated SoC.
        self.soc_percent -= soc_reduction

        # Clamp insignificant numerical errors to the lower limit.
        self.soc_percent = max(
            self.min_soc_percent,
            self.soc_percent,
        )

        # Update the accumulated energy counter.
        self.total_energy_consumed_kwh += requested_energy

        # Record the operation.
        self.operation_count += 1

        # Re-check the resulting state.
        self.check_battery_status()

        # Return the updated state.
        return {
            "battery_name": self.name,
            "energy_consumed_kwh": requested_energy,
            "energy_consumed_wh": requested_energy * 1000.0,
            "soc_percent": self.soc_percent,
            "stored_energy_kwh": self.stored_energy_kwh,
            "available_energy_kwh": self.available_energy_kwh,
            "estimated_voltage_v": self.estimated_voltage_v,
            "temperature_c": self.temperature_c,
            "available": self.check_battery_status(),
        }

    # ========================================================
    # SECTION 7: ADDING ENERGY
    # ========================================================

    def add_energy(
        self,
        input_energy_kwh,
        duration_s=None,
        apply_charge_efficiency=True,
    ):
        """
        Simulate charging the battery or adding recovered energy.

        Parameters:
            input_energy_kwh:
                Energy supplied to the charging process, in kWh.

            duration_s:
                Optional charging duration in seconds.

            apply_charge_efficiency:
                If True, only the configured fraction of input energy
                is added to stored energy.

        Returns:
            A dictionary containing input energy, stored energy added,
            updated SoC, and unused input energy.

        The operation is rejected if the battery is unavailable or
        the supplied average charging power exceeds its configured
        simulated charging-power limit.
        """

        # Validate the incoming energy.
        input_energy = validate_non_negative(
            input_energy_kwh,
            "input_energy_kwh",
        )

        # Validate the optional duration.
        if duration_s is not None:
            duration_s = validate_positive(
                duration_s,
                "duration_s",
            )

        # Check whether the battery is eligible to receive energy.
        if not self.check_battery_status():
            raise RuntimeError(
                f"{self.name} is unavailable: "
                f"{', '.join(self.faults)}"
            )

        # Determine the average incoming power if duration is known.
        if duration_s is not None:
            input_power_w = (
                input_energy * 3_600_000.0 / duration_s
            )
        else:
            input_power_w = None

        # Enforce the configured charging-power limit.
        if (
            input_power_w is not None
            and self.max_charge_power_w is not None
            and input_power_w
            > self.max_charge_power_w + NUMERICAL_TOLERANCE
        ):
            raise ValueError(
                f"{self.name}: requested charging power exceeds "
                "the configured simulation limit."
            )

        # Apply the assumed charging efficiency.
        if apply_charge_efficiency:
            potential_stored_energy = (
                input_energy * self.charge_efficiency
            )
        else:
            potential_stored_energy = input_energy

        # Calculate the remaining storage capacity.
        remaining_capacity = self.remaining_charge_capacity_kwh

        # Limit stored energy to the remaining capacity.
        actual_stored_energy = min(
            potential_stored_energy,
            remaining_capacity,
        )

        # Calculate the corresponding increase in SoC.
        soc_increase = (
            actual_stored_energy / self.capacity_kwh * 100.0
        )

        # Update the simulated SoC.
        self.soc_percent += soc_increase

        # Clamp floating-point errors at the upper limit.
        self.soc_percent = min(
            self.max_soc_percent,
            self.soc_percent,
        )

        # Update the accumulated stored-energy counter.
        self.total_energy_added_kwh += actual_stored_energy

        # Estimate energy not stored due to conversion losses
        # or the configured capacity limit.
        unused_input_energy = max(
            0.0,
            input_energy - actual_stored_energy,
        )

        # Record the operation.
        self.operation_count += 1

        # Re-evaluate the resulting state.
        self.check_battery_status()

        # Return the charging summary.
        return {
            "battery_name": self.name,
            "input_energy_kwh": input_energy,
            "input_energy_wh": input_energy * 1000.0,
            "stored_energy_added_kwh": actual_stored_energy,
            "stored_energy_added_wh": actual_stored_energy * 1000.0,
            "unused_input_energy_kwh": unused_input_energy,
            "soc_percent": self.soc_percent,
            "stored_energy_kwh": self.stored_energy_kwh,
            "remaining_charge_capacity_kwh": (
                self.remaining_charge_capacity_kwh
            ),
            "estimated_voltage_v": self.estimated_voltage_v,
            "temperature_c": self.temperature_c,
            "available": self.check_battery_status(),
        }

    # ========================================================
    # SECTION 8: TEMPERATURE UPDATES
    # ========================================================

    def update_temperature(self, new_temperature_c):
        """
        Update the simulated temperature.

        The method accepts a supplied value. It does not model heat
        generation, cooling, or real battery thermal dynamics.
        """

        # Validate the new temperature.
        temperature = validate_number(
            new_temperature_c,
            "new_temperature_c",
        )

        # Store the simulated temperature.
        self.temperature_c = temperature

        # Re-check operating eligibility.
        self.check_battery_status()

        return self.temperature_c

    # ========================================================
    # SECTION 9: SIMULATED FAULT MANAGEMENT
    # ========================================================

    def set_fault(self, fault_message):
        """
        Add a simulated fault to the battery.

        This can be used to test how the future battery manager
        responds when a battery becomes unavailable.
        """

        # Require a meaningful fault description.
        if not isinstance(fault_message, str):
            raise TypeError("Fault description must be a string.")

        if not fault_message.strip():
            raise ValueError("Fault description cannot be empty.")

        # Avoid recording the same fault repeatedly.
        if fault_message not in self.faults:
            self.faults.append(fault_message)

        return self.check_battery_status()

    def clear_fault(self, fault_message):
        """
        Remove a simulated fault from the fault list.

        Clearing a software flag does not repair a physical battery.
        """

        # Remove the requested fault if it exists.
        if fault_message in self.faults:
            self.faults.remove(fault_message)

        # Re-evaluate the battery's operating state.
        return self.check_battery_status()

    def enable(self):
        """Enable this battery in the software simulation."""

        self.enabled = True

        return self.check_battery_status()

    def disable(self):
        """Disable this battery in the software simulation."""

        self.enabled = False

        return self.check_battery_status()

    # ========================================================
    # SECTION 10: BATTERY STATUS CHECK
    # ========================================================

    def check_battery_status(self):
        """
        Evaluate whether the battery is eligible for simulated use.

        Checks:
            1. Enabled state.
            2. Existing simulated faults.
            3. State-of-charge limits.
            4. Temperature limits.
            5. Illustrative voltage limits.

        Returns:
            True if all checks pass; otherwise False.

        This function is not a replacement for a physical BMS.
        """

        # Collect newly detected operating-limit violations.
        detected_faults = []

        # A disabled battery is not eligible for use.
        if not self.enabled:
            detected_faults.append("Battery disabled")

        # Check the configured state-of-charge limits.
        if self.soc_percent < self.min_soc_percent:
            detected_faults.append("SoC below minimum")

        if self.soc_percent > self.max_soc_percent:
            detected_faults.append("SoC above maximum")

        # Check the configured temperature limits.
        if self.temperature_c < self.min_temperature_c:
            detected_faults.append("Temperature below limit")

        if self.temperature_c > self.max_temperature_c:
            detected_faults.append("Temperature above limit")

        # Estimate voltage using the illustrative voltage model.
        voltage = self.estimated_voltage_v

        # Check the voltage limits.
        if voltage < self.min_voltage_v:
            detected_faults.append("Estimated voltage below limit")

        if voltage > self.max_voltage_v:
            detected_faults.append("Estimated voltage above limit")

        # Preserve manually injected or externally reported faults.
        # Faults that are automatically detected are recalculated.
        manual_faults = [
            fault for fault in self.faults
            if not fault.startswith("AUTO:")
        ]

        # Store the current automatically detected faults.
        automatic_faults = [
            f"AUTO: {fault}" for fault in detected_faults
        ]

        # Combine both categories without duplicate entries.
        self.faults = manual_faults + automatic_faults

        # The battery is eligible only when no faults remain.
        return len(self.faults) == 0

    @property
    def is_available(self):
        """Return the current simulated eligibility state."""

        return self.check_battery_status()

    # ========================================================
    # SECTION 11: EXPORTING THE BATTERY STATE
    # ========================================================

    def get_state(self):
        """
        Return the current battery state as a dictionary.

        This structure is convenient for CSV logging, dashboards,
        and integration with the energy simulator.
        """

        # Refresh the operating status before exporting it.
        available = self.check_battery_status()

        return {
            "name": self.name,
            "capacity_kwh": self.capacity_kwh,
            "nominal_voltage_v": self.nominal_voltage_v,
            "estimated_voltage_v": self.estimated_voltage_v,
            "soc_percent": self.soc_percent,
            "stored_energy_kwh": self.stored_energy_kwh,
            "stored_energy_wh": self.stored_energy_wh,
            "available_energy_kwh": self.available_energy_kwh,
            "available_energy_wh": self.available_energy_wh,
            "remaining_charge_capacity_kwh": (
                self.remaining_charge_capacity_kwh
            ),
            "temperature_c": self.temperature_c,
            "enabled": self.enabled,
            "available": available,
            "faults": list(self.faults),
            "operation_count": self.operation_count,
            "total_energy_consumed_kwh": (
                self.total_energy_consumed_kwh
            ),
            "total_energy_added_kwh": (
                self.total_energy_added_kwh
            ),
        }

    def print_status(self):
        """Print a readable summary of the current battery state."""

        state = self.get_state()

        print("\n" + "-" * 54)
        print(f"BATTERY STATUS: {state['name']}")
        print("-" * 54)

        print(f"Capacity:                 {state['capacity_kwh']:.3f} kWh")
        print(f"Nominal voltage:          {state['nominal_voltage_v']:.2f} V")
        print(f"Estimated voltage:        {state['estimated_voltage_v']:.2f} V")
        print(f"State of charge:          {state['soc_percent']:.2f}%")
        print(f"Stored energy:            {state['stored_energy_kwh']:.3f} kWh")
        print(f"Available energy:         {state['available_energy_kwh']:.3f} kWh")
        print(f"Temperature:              {state['temperature_c']:.2f} °C")
        print(f"Enabled:                  {state['enabled']}")
        print(f"Eligible for use:         {state['available']}")
        print(f"Operations:               {state['operation_count']}")
        print(f"Energy consumed:          {state['total_energy_consumed_kwh']:.3f} kWh")
        print(f"Energy added:             {state['total_energy_added_kwh']:.3f} kWh")

        # Display any operating faults.
        if state["faults"]:
            print("Faults:")
            for fault in state["faults"]:
                print(f"  - {fault}")
        else:
            print("Faults:                   None")

        print("-" * 54)


# ============================================================
# SECTION 12: CREATING THE TWO FLUXXWAVE BATTERIES
# ============================================================

def create_battery_a():
    """
    Create an example Battery A.

    The parameters are illustrative software settings. Replace them
    with documented specifications if a particular battery is selected.
    """

    return Battery(
        name="Battery A",
        capacity_kwh=2.0,
        nominal_voltage_v=48.0,
        soc_percent=80.0,
        temperature_c=25.0,
        min_soc_percent=20.0,
        max_soc_percent=100.0,
        min_temperature_c=0.0,
        max_temperature_c=45.0,
        min_voltage_v=30.0,
        max_voltage_v=48.0,
        voltage_at_zero_soc_v=38.4,
        max_discharge_power_w=1500.0,
        max_charge_power_w=1000.0,
        charge_efficiency=0.95,
    )


def create_battery_b():
    """
    Create an example Battery B with independent initial conditions.
    """

    return Battery(
        name="Battery B",
        capacity_kwh=2.0,
        nominal_voltage_v=48.0,
        soc_percent=90.0,
        temperature_c=24.0,
        min_soc_percent=20.0,
        max_soc_percent=100.0,
        min_temperature_c=0.0,
        max_temperature_c=45.0,
        min_voltage_v=30.0,
        max_voltage_v=48.0,
        voltage_at_zero_soc_v=38.4,
        max_discharge_power_w=1500.0,
        max_charge_power_w=1000.0,
        charge_efficiency=0.95,
    )


# ============================================================
# SECTION 13: COMPARING BOTH BATTERIES
# ============================================================

def compare_batteries(battery_a, battery_b):
    """
    Compare the current states of Battery A and Battery B.

    Returns:
        A dictionary containing the individual states and a simple
        comparison of available energy and operating eligibility.

    This function does not switch between the batteries.
    Switching belongs in battery_manager.py.
    """

    # Obtain fresh state information from both batteries.
    state_a = battery_a.get_state()
    state_b = battery_b.get_state()

    # Calculate the difference in available energy.
    energy_difference = (
        state_a["available_energy_kwh"]
        - state_b["available_energy_kwh"]
    )

    # Return the comparison.
    return {
        "battery_a": state_a,
        "battery_b": state_b,
        "available_energy_difference_kwh": energy_difference,
        "battery_a_available": state_a["available"],
        "battery_b_available": state_b["available"],
        "both_available": (
            state_a["available"] and state_b["available"]
        ),
    }


# ============================================================
# SECTION 14: EXAMPLE SIMULATION
# ============================================================

def run_demo():
    """
    Demonstrate independent battery operation.

    The values are simulated. No physical battery is connected.
    """

    print("\n" + "=" * 60)
    print("       FLUXXWAVE BATTERY SIMULATION")
    print("=" * 60)

    # Create two independent battery objects.
    battery_a = create_battery_a()
    battery_b = create_battery_b()

    # Display their initial states.
    print("\nINITIAL STATES")
    battery_a.print_status()
    battery_b.print_status()

    # Simulate a load consuming 0.30 kWh from Battery A.
    print("\nSTEP 1: Simulated energy consumption from Battery A")

    result_a = battery_a.consume_energy(
        energy_kwh=0.30,
        duration_s=1800.0,
    )

    print(
        f"Battery A SoC after consumption: "
        f"{result_a['soc_percent']:.2f}%"
    )

    # Simulate energy being added to Battery B.
    print("\nSTEP 2: Simulated charging of Battery B")

    result_b = battery_b.add_energy(
        input_energy_kwh=0.20,
        duration_s=1800.0,
    )

    print(
        f"Battery B SoC after charging: "
        f"{result_b['soc_percent']:.2f}%"
    )

    # Display the updated states.
    print("\nUPDATED STATES")
    battery_a.print_status()
    battery_b.print_status()

    # Compare both batteries.
    print("\nSTEP 3: Comparing battery availability")

    comparison = compare_batteries(
        battery_a,
        battery_b,
    )

    print(
        "Battery A available:",
        comparison["battery_a_available"],
    )
    print(
        "Battery B available:",
        comparison["battery_b_available"],
    )
    print(
        "Available energy difference (A - B): "
        f"{comparison['available_energy_difference_kwh']:.3f} kWh"
    )

    # Demonstrate a simulated fault on Battery B.
    print("\nSTEP 4: Demonstrating a simulated fault")

    battery_b.set_fault("SIMULATED_TEST_FAULT")

    print("Battery B available after fault:", battery_b.is_available)
    print("Battery B faults:", battery_b.faults)

    # Clear the test fault.
    battery_b.clear_fault("SIMULATED_TEST_FAULT")

    print("Battery B available after clearing test fault:", battery_b.is_available)

    # Print the final battery states.
    print("\nFINAL STATES")
    battery_a.print_status()
    battery_b.print_status()

    print("\nBattery simulation completed.")
    print("All operations were simulated in software.")

    return battery_a, battery_b


# ============================================================
# SECTION 15: PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    # Run the example only when this file is executed directly.
    run_demo()
