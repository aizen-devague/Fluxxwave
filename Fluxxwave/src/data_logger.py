
"""
data_logger.py
============================================================
FLUXXWAVE EV PROJECT — DATA RECORDING MODULE

PURPOSE
-------
Record simulation outputs in a consistent, reproducible format.

RESPONSIBILITIES
----------------
1. Record timestamps and simulation component states.
2. Store voltage, current, power, SoC, and energy estimates
   when the source actually provides them.
3. Record battery-switching events.
4. Record supervisory warnings and simulated faults.
5. Export samples and events to CSV.
6. Load previously saved CSV datasets.
7. Preserve the distinction between simulated and measured data.

DEPENDENCIES
------------
Python standard library only.

DATA INTEGRITY
--------------
- Missing values are written as empty CSV fields.
- Values from the simulation are labelled as simulated.
- This module does not claim that simulated values are
  measured hardware data.
- Event logs and sample logs are stored separately.

SAFETY
------
This is a data-recording module for software simulations.
It does not connect to real vehicle sensors or hardware.
============================================================
"""

import csv
import json
import math

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================
# 1. DEFAULT CONFIGURATION
# ============================================================

DEFAULT_OUTPUT_DIRECTORY = "data/logs"

# Each record receives a provenance label.
SOURCE_SIMULATION = "simulation"
SOURCE_MEASURED = "measured_hardware"

# This project currently records simulation data only.
# A future hardware logger would need an explicitly designed
# and validated acquisition interface before using the second
# label.
ALLOWED_DATA_SOURCES = {
    SOURCE_SIMULATION,
    SOURCE_MEASURED,
}

# Version the log schema to help identify changes between runs.
LOGGER_SCHEMA_VERSION = "1.0"


# ============================================================
# 2. GENERAL HELPERS
# ============================================================

def utc_timestamp():
    """
    Return the current UTC timestamp in ISO 8601 format.

    UTC timestamps make datasets easier to compare across
    computers and time zones.
    """

    return datetime.now(timezone.utc).isoformat(
        timespec="milliseconds"
    )


def validate_data_source(source):
    """
    Validate the provenance label.

    A caller must explicitly identify whether a record is
    simulated or measured. This logger does not automatically
    convert one type into the other.
    """

    if source not in ALLOWED_DATA_SOURCES:
        raise ValueError(
            f"Invalid data source: {source!r}. "
            f"Choose one of {sorted(ALLOWED_DATA_SOURCES)}."
        )

    return source


def safe_number(value, field_name="value"):
    """
    Convert a numeric value to float.

    None and empty strings remain missing values.
    NaN and infinity are rejected because they can undermine
    downstream analysis.
    """

    if value is None or value == "":
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(
            f"{field_name} must be numeric or missing."
        )

    if not math.isfinite(number):
        raise ValueError(
            f"{field_name} must be finite."
        )

    return number


def csv_safe_value(value):
    """
    Convert a Python value into a CSV-compatible value.

    Nested dictionaries and lists are stored as JSON strings,
    so structured component states can be preserved in CSV.
    """

    if value is None:
        return ""

    if isinstance(value, bool):
        return str(value)

    if isinstance(value, (dict, list, tuple)):
        return json.dumps(
            value,
            ensure_ascii=False,
            default=str,
        )

    if isinstance(value, float):
        if not math.isfinite(value):
            return ""
        return value

    return value


def parse_csv_value(value):
    """
    Interpret an empty CSV field as missing.

    Other values remain strings because CSV does not preserve
    original Python types automatically.
    """

    if value == "":
        return None

    return value


# ============================================================
# 3. DATA LOGGER CLASS
# ============================================================

class DataLogger:
    """
    Manage simulation samples and system events.

    The logger keeps records in memory until save_csv() is
    called. Samples and events are exported to separate files.

    Parameters
    ----------
    output_directory:
        Directory in which CSV files will be stored.

    run_id:
        Optional identifier for a simulation run.

    data_source:
        Provenance label. Defaults to "simulation".
    """

    def __init__(
        self,
        output_directory=DEFAULT_OUTPUT_DIRECTORY,
        run_id=None,
        data_source=SOURCE_SIMULATION,
    ):

        self.output_directory = Path(output_directory)

        # Create an ID for this run if the caller did not
        # supply one.
        self.run_id = (
            str(run_id)
            if run_id is not None
            else datetime.now(timezone.utc).strftime(
                "fluxxwave_%Y%m%d_%H%M%S"
            )
        )

        self.data_source = validate_data_source(
            data_source
        )

        # Samples and events are separate datasets because
        # they represent different kinds of information.
        self.samples: List[Dict[str, Any]] = []

        self.events: List[Dict[str, Any]] = []

        # Preserve logger-level metadata for exports.
        self.metadata = {
            "schema_version": LOGGER_SCHEMA_VERSION,
            "run_id": self.run_id,
            "data_source": self.data_source,
            "created_at_utc": utc_timestamp(),
        }


    # ========================================================
    # 4. RECORD ONE SAMPLE
    # ========================================================

    def record_sample(
        self,
        sample,
        source=None,
        timestamp=None,
    ):
        """
        Record one sample of the system state.

        Parameters
        ----------
        sample:
            Dictionary of values from the simulator or a
            future, explicitly validated data-acquisition layer.

        source:
            Optional provenance override.

        timestamp:
            Optional timestamp. If omitted, current UTC time
            is recorded.

        Returns
        -------
        dict
            The normalized sample stored in memory.

        Suggested fields
        ----------------
        simulation_time_seconds
        active_battery_id
        battery_a_soc_percent
        battery_b_soc_percent
        battery_a_voltage_v
        battery_b_voltage_v
        battery_a_current_a
        battery_b_current_a
        solar_power_w
        regenerative_power_w
        vehicle_demand_w
        solar_energy_kwh
        regenerative_energy_kwh
        vehicle_demand_kwh
        """

        if not isinstance(sample, dict):
            raise TypeError(
                "sample must be a dictionary."
            )

        record_source = validate_data_source(
            source or self.data_source
        )

        # Copy the input so logging does not mutate the
        # simulator's original dictionary.
        record = dict(sample)

        # Standard metadata is added to every sample.
        record["timestamp_utc"] = (
            timestamp or utc_timestamp()
        )

        record["run_id"] = self.run_id

        record["data_source"] = record_source

        record["schema_version"] = (
            LOGGER_SCHEMA_VERSION
        )

        # Prevent missing sensor/model outputs from being
        # represented as invented numerical values.
        #
        # None stays None and becomes an empty CSV field.
        #
        # Voltage and current fields are not calculated here.
        # They are recorded only when supplied by the caller.
        self.samples.append(record)

        return record


    # ========================================================
    # 5. RECORD A SYSTEM EVENT
    # ========================================================

    def record_event(
        self,
        event_type,
        message,
        severity="INFO",
        component=None,
        details=None,
        source=None,
        timestamp=None,
    ):
        """
        Record a warning, error, battery switch, or other event.

        Parameters
        ----------
        event_type:
            Machine-readable event name, such as
            "SWITCH_SUCCESS" or "ENERGY_BALANCE_WARNING".

        message:
            Human-readable explanation.

        severity:
            INFO, WARNING, or ERROR.

        component:
            Component associated with the event.

        details:
            Optional dictionary of additional information.
        """

        record_source = validate_data_source(
            source or self.data_source
        )

        severity = str(severity).upper()

        if severity not in {"INFO", "WARNING", "ERROR"}:
            raise ValueError(
                "severity must be INFO, WARNING, or ERROR."
            )

        event = {
            "timestamp_utc": (
                timestamp or utc_timestamp()
            ),
            "run_id": self.run_id,
            "schema_version": LOGGER_SCHEMA_VERSION,
            "data_source": record_source,
            "event_type": str(event_type),
            "severity": severity,
            "component": (
                str(component)
                if component is not None
                else ""
            ),
            "message": str(message),
            "details": details if details is not None else {},
        }

        self.events.append(event)

        return event


    # ========================================================
    # 6. RECORD A BATTERY SWITCHING EVENT
    # ========================================================

    def record_switching_event(self, event):
        """
        Convert a BatteryManager event into a standard event.

        Expected fields from battery_manager.py include:
            timestamp
            event_type
            from_battery
            to_battery
            success
            controller_status
            reason

        The original event is retained in the details field.
        """

        if not isinstance(event, dict):
            raise TypeError(
                "Switching event must be a dictionary."
            )

        event_type = event.get(
            "event_type",
            "BATTERY_MANAGER_EVENT",
        )

        success = event.get("success")

        if success is True:
            severity = "INFO"

        elif success is False:
            severity = "WARNING"

        else:
            severity = "INFO"

        message = event.get(
            "reason",
            "Battery manager event recorded.",
        )

        # Keep the original timestamp if the manager supplied one.
        original_timestamp = event.get("timestamp")

        return self.record_event(
            event_type=event_type,
            message=message,
            severity=severity,
            component="battery_manager",
            details=event,
            timestamp=original_timestamp,
        )


    # ========================================================
    # 7. RECORD A CONTROLLER EVENT
    # ========================================================

    def record_controller_event(self, event):
        """
        Convert an event from controller.py into a log record.

        Expected fields include:
            timestamp
            event_type
            severity
            message
            details
        """

        if not isinstance(event, dict):
            raise TypeError(
                "Controller event must be a dictionary."
            )

        return self.record_event(
            event_type=event.get(
                "event_type",
                "CONTROLLER_EVENT",
            ),
            message=event.get(
                "message",
                "Controller event recorded.",
            ),
            severity=event.get(
                "severity",
                "INFO",
            ),
            component="controller",
            details=event.get("details", {}),
            timestamp=event.get("timestamp"),
        )


    # ========================================================
    # 8. RECORD A SIMULATION STEP
    # ========================================================

    def record_simulation_step(
        self,
        step_result,
        simulation_state=None,
    ):
        """
        Extract useful values from run_simulation_step().

        This method records the fields the current simulation
        actually provides. Voltage and current are left missing
        unless a source explicitly supplies them.

        Parameters
        ----------
        step_result:
            Dictionary returned by run_simulation_step().

        simulation_state:
            Optional full state dictionary returned by
            initialize_simulation() or run_simulation().

        Returns
        -------
        dict
            The recorded sample.
        """

        if not isinstance(step_result, dict):
            raise TypeError(
                "step_result must be a dictionary."
            )

        power = step_result.get("power", {})
        energy = step_result.get("energy", {})
        battery = step_result.get("battery", {})
        load = step_result.get("load", {})
        regen = step_result.get("regenerative", {})

        # Build a flat record that is easy to analyze in CSV.
        sample = {
            "simulation_time_seconds": (
                step_result.get("time_seconds")
            ),

            # Battery selection and SoC.
            "active_battery_id": (
                battery.get("active_battery_id")
            ),
            "controller_status": (
                battery.get("controller_status")
            ),
            "battery_a_soc_percent": (
                battery.get("battery_a_soc_percent")
            ),
            "battery_b_soc_percent": (
                battery.get("battery_b_soc_percent")
            ),

            # Stored and available energy.
            "battery_a_stored_kwh": (
                battery.get("battery_a_stored_kwh")
            ),
            "battery_b_stored_kwh": (
                battery.get("battery_b_stored_kwh")
            ),
            "battery_a_available_kwh": (
                battery.get("battery_a_available_kwh")
            ),
            "battery_b_available_kwh": (
                battery.get("battery_b_available_kwh")
            ),

            # Voltage/current are intentionally missing unless
            # a model or data-acquisition layer supplies them.
            "battery_a_voltage_v": None,
            "battery_b_voltage_v": None,
            "battery_a_current_a": None,
            "battery_b_current_a": None,

            # Power estimates.
            "speed_mps": power.get("speed_mps"),
            "speed_kmh": power.get("speed_kmh"),
            "irradiance_w_m2": power.get("irradiance_w_m2"),
            "solar_power_w": power.get("solar_power_w"),
            "regenerative_power_w": (
                power.get("regenerative_power_w")
            ),
            "vehicle_demand_w": (
                power.get("vehicle_demand_w")
            ),
            "traction_power_w": (
                power.get("traction_power_w")
            ),
            "auxiliary_power_w": (
                power.get("auxiliary_power_w")
            ),

            # Energy estimates for this step.
            "solar_energy_kwh": (
                energy.get("solar_generated_kwh")
            ),
            "regenerative_energy_kwh": (
                energy.get("regenerative_electrical_kwh")
            ),
            "vehicle_demand_kwh": (
                energy.get("vehicle_demand_kwh")
            ),
            "battery_energy_removed_kwh": (
                energy.get("battery_energy_removed_kwh")
            ),
            "battery_energy_stored_kwh": (
                energy.get("battery_energy_stored_kwh")
            ),

            # Energy losses and unserved demand.
            "battery_charge_loss_kwh": (
                energy.get("battery_charge_loss_kwh")
            ),
            "battery_discharge_loss_kwh": (
                energy.get("battery_discharge_loss_kwh")
            ),
            "curtailed_solar_kwh": (
                energy.get("curtailed_solar_kwh")
            ),
            "curtailed_regenerative_kwh": (
                energy.get("curtailed_regenerative_kwh")
            ),
            "unmet_vehicle_demand_kwh": (
                energy.get("unmet_vehicle_demand_kwh")
            ),
            "balance_error_kwh": (
                energy.get("balance_error_kwh")
            ),

            # Preserve the source classification.
            "measurement_note": (
                "Values are simulation estimates, not "
                "measured hardware data."
            ),
        }

        # Include battery information that may be available
        # only in the full simulation state.
        if simulation_state is not None:

            batteries = simulation_state.get(
                "batteries",
                {},
            )

            for battery_id in ("A", "B"):

                battery_object = batteries.get(
                    battery_id
                )

                if battery_object is None:
                    continue

                # Record the battery's estimated voltage only
                # if the model explicitly exposes it.
                voltage = getattr(
                    battery_object,
                    "estimated_voltage_v",
                    None,
                )

                sample[
                    f"battery_{battery_id.lower()}_voltage_v"
                ] = voltage

                # The current Battery class does not calculate
                # current from a physical sensor. Do not infer
                # current from nominal voltage.
                #
                # A future model may supply an explicitly
                # labelled estimated_current_a field.
                current = getattr(
                    battery_object,
                    "estimated_current_a",
                    None,
                )

                sample[
                    f"battery_{battery_id.lower()}_current_a"
                ] = current

        return self.record_sample(
            sample,
            source=SOURCE_SIMULATION,
        )


    # ========================================================
    # 9. IMPORT EVENTS FROM THE EXISTING MANAGER
    # ========================================================

    def import_battery_manager_events(
        self,
        battery_manager,
        start_index=0,
    ):
        """
        Import switching events from BatteryManager.

        start_index prevents repeatedly importing the entire
        event history. The caller can store the returned index
        and pass it during the next import.
        """

        events = getattr(
            battery_manager,
            "switching_events",
            [],
        )

        if start_index < 0:
            raise ValueError(
                "start_index cannot be negative."
            )

        for event in events[start_index:]:
            self.record_switching_event(event)

        return len(events)


    # ========================================================
    # 10. IMPORT EVENTS FROM THE SUPERVISORY CONTROLLER
    # ========================================================

    def import_controller_events(
        self,
        controller,
        start_index=0,
    ):
        """
        Import controller events such as warnings and errors.

        Returns the total number of controller events so the
        caller can track its next starting index.
        """

        events = getattr(
            controller,
            "events",
            [],
        )

        if start_index < 0:
            raise ValueError(
                "start_index cannot be negative."
            )

        for event in events[start_index:]:
            self.record_controller_event(event)

        return len(events)


    # ========================================================
    # 11. SAVE RECORDS TO CSV
    # ========================================================

    def _save_records(self, records, output_path):
        """
        Internal helper for writing a list of dictionaries.

        The CSV header is the union of the keys in all records.
        This allows optional fields to be missing in some rows.
        """

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if not records:

            # An empty dataset has no known data columns.
            # Create a valid file with the basic metadata header.
            with output_path.open(
                "w",
                newline="",
                encoding="utf-8",
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "timestamp_utc",
                    "run_id",
                    "schema_version",
                    "data_source",
                ])

            return str(output_path)

        # Preserve first-seen column order while including
        # additional fields introduced by later records.
        fieldnames = []

        seen = set()

        for record in records:

            for key in record.keys():

                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)

        with output_path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
                extrasaction="ignore",
            )

            writer.writeheader()

            for record in records:

                safe_record = {
                    key: csv_safe_value(
                        record.get(key)
                    )
                    for key in fieldnames
                }

                writer.writerow(safe_record)

        return str(output_path)


    def save_csv(
        self,
        samples_filename="samples.csv",
        events_filename="events.csv",
        metadata_filename="metadata.json",
    ):
        """
        Save samples, events, and run metadata.

        Files are written under output_directory.

        Returns
        -------
        dict
            Paths of the saved files.
        """

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        samples_path = (
            self.output_directory / samples_filename
        )

        events_path = (
            self.output_directory / events_filename
        )

        metadata_path = (
            self.output_directory / metadata_filename
        )

        saved_samples = self._save_records(
            self.samples,
            samples_path,
        )

        saved_events = self._save_records(
            self.events,
            events_path,
        )

        # Store a compact metadata summary for reproducibility.
        metadata = dict(self.metadata)

        metadata["sample_count"] = len(self.samples)

        metadata["event_count"] = len(self.events)

        metadata["saved_at_utc"] = utc_timestamp()

        with metadata_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                metadata,
                file,
                indent=4,
                ensure_ascii=False,
            )

        print("\nFluxxwave data export complete.")

        print(
            f"Samples: {saved_samples}"
        )

        print(
            f"Events: {saved_events}"
        )

        print(
            f"Metadata: {metadata_path}"
        )

        return {
            "samples": saved_samples,
            "events": saved_events,
            "metadata": str(metadata_path),
        }


    # ========================================================
    # 12. LOAD A CSV DATASET
    # ========================================================

    @staticmethod
    def load_csv(filename):
        """
        Load a CSV file as a list of dictionaries.

        Empty fields become None.
        Other values remain strings to avoid guessing types.

        Example
        -------
        rows = DataLogger.load_csv("data/logs/samples.csv")
        """

        input_path = Path(filename)

        if not input_path.exists():
            raise FileNotFoundError(
                f"CSV file not found: {input_path}"
            )

        with input_path.open(
            "r",
            newline="",
            encoding="utf-8-sig",
        ) as file:

            reader = csv.DictReader(file)

            records = []

            for row in reader:

                normalized_row = {
                    key: parse_csv_value(value)
                    for key, value in row.items()
                }

                records.append(normalized_row)

        return records


    # ========================================================
    # 13. CLEAR IN-MEMORY RECORDS
    # ========================================================

    def clear(self):
        """
        Clear samples and events from memory.

        This does not delete previously exported CSV files.
        """

        self.samples.clear()

        self.events.clear()

        print(
            "In-memory sample and event histories cleared."
        )


    # ========================================================
    # 14. PRINT LOGGER STATUS
    # ========================================================

    def print_status(self):
        """Display a summary of the current logger state."""

        print("\n" + "=" * 58)
        print("FLUXXWAVE — DATA LOGGER")
        print("=" * 58)

        print(f"Run ID       : {self.run_id}")

        print(f"Data source  : {self.data_source}")

        print(
            f"Sample count : {len(self.samples)}"
        )

        print(
            f"Event count  : {len(self.events)}"
        )

        print(
            f"Output folder: {self.output_directory}"
        )

        print(
            f"Schema       : {LOGGER_SCHEMA_VERSION}"
        )

        print("=" * 58)


# ============================================================
# 15. MODULE-LEVEL CONVENIENCE FUNCTIONS
# ============================================================

def record_sample(logger, sample, source=None):
    """
    Convenience wrapper around DataLogger.record_sample().
    """

    return logger.record_sample(
        sample,
        source=source,
    )


def record_event(
    logger,
    event_type,
    message,
    severity="INFO",
    component=None,
    details=None,
):
    """
    Convenience wrapper around DataLogger.record_event().
    """

    return logger.record_event(
        event_type=event_type,
        message=message,
        severity=severity,
        component=component,
        details=details,
    )


def save_csv(logger, **kwargs):
    """
    Convenience wrapper around DataLogger.save_csv().
    """

    return logger.save_csv(**kwargs)


def load_csv(filename):
    """
    Convenience wrapper around DataLogger.load_csv().
    """

    return DataLogger.load_csv(filename)


# ============================================================
# 16. DEMONSTRATION
# ============================================================

def main():
    """
    Demonstrate logging, exporting, and reloading data.

    The example values below are explicitly illustrative
    simulation data, not real vehicle measurements.
    """

    logger = DataLogger(
        output_directory="data/logs",
        run_id="fluxxwave_demo",
        data_source=SOURCE_SIMULATION,
    )

    # --------------------------------------------------------
    # DEMO 1: Record a simulation sample.
    # --------------------------------------------------------

    sample = {
        "simulation_time_seconds": 60.0,

        "active_battery_id": "A",

        "battery_a_soc_percent": 79.5,
        "battery_b_soc_percent": 90.0,

        "battery_a_voltage_v": None,
        "battery_b_voltage_v": None,

        "battery_a_current_a": None,
        "battery_b_current_a": None,

        "solar_power_w": 250.0,
        "regenerative_power_w": 0.0,
        "vehicle_demand_w": 700.0,

        "solar_energy_kwh": 0.004167,
        "regenerative_energy_kwh": 0.0,
        "vehicle_demand_kwh": 0.011667,

        "measurement_note": (
            "Illustrative simulation values, not measured data."
        ),
    }

    logger.record_sample(sample)

    # --------------------------------------------------------
    # DEMO 2: Record a successful battery switch.
    # --------------------------------------------------------

    logger.record_event(
        event_type="SWITCH_SUCCESS",
        message="Simulated switch from Battery A to Battery B.",
        severity="INFO",
        component="battery_manager",
        details={
            "from_battery": "A",
            "to_battery": "B",
            "simulated": True,
        },
    )

    # --------------------------------------------------------
    # DEMO 3: Record a simulated warning.
    # --------------------------------------------------------

    logger.record_event(
        event_type="ENERGY_BALANCE_WARNING",
        message="Illustrative energy-balance warning.",
        severity="WARNING",
        component="energy_simulator",
        details={
            "balance_error_kwh": 0.00001,
            "simulated": True,
        },
    )

    # --------------------------------------------------------
    # DEMO 4: Export all records.
    # --------------------------------------------------------

    logger.print_status()

    exported_paths = logger.save_csv()

    # --------------------------------------------------------
    # DEMO 5: Reload the saved sample CSV.
    # --------------------------------------------------------

    loaded_samples = logger.load_csv(
        exported_paths["samples"]
    )

    print(
        "\nReloaded sample count:",
        len(loaded_samples),
    )

    if loaded_samples:
        print("First reloaded sample:")

        for key, value in loaded_samples[0].items():
            print(f"  {key}: {value}")


# ============================================================
# 17. SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
