
"""
battery_manager.py
============================================================
Fluxxwave EV Project — Dual-Battery Switching Manager

PURPOSE
-------
This module manages two simulated batteries and decides which
battery should be active.

Main responsibilities:
1. Select an eligible active battery.
2. Monitor the configurable switching threshold.
3. Validate the alternate battery before switching.
4. Simulate successful and failed switching operations.
5. Apply hysteresis and a minimum switching interval.
6. Handle the situation where neither battery is eligible.
7. Record switching events and export them to CSV.

DEPENDENCY
----------
This module expects battery.py to contain the Battery class
and the following attributes/methods:

    battery.soc_percent
    battery.min_soc_percent
    battery.enabled
    battery.faults
    battery.is_available()

SAFETY NOTE
-----------
This is a software simulation, not a real battery controller.
It must not directly control a real EV traction battery.

Real battery systems require an engineered battery-management
system, electrical protection, contactor interlocks, isolation
monitoring, current sensing, and hardware-level fault handling.
============================================================
"""

# datetime supplies timestamps for the switching event log.
from datetime import datetime

# csv writes the event history to a spreadsheet-compatible file.
import csv

# Path provides convenient handling of output file paths.
from pathlib import Path

# Optional provides type hints for values that may be absent.
from typing import Optional, Dict, List, Any


# ============================================================
# 1. DEFAULT CONFIGURATION
# ============================================================

# The active battery should normally be replaced when its
# state of charge reaches or falls below this percentage.
DEFAULT_SWITCH_THRESHOLD = 20.0

# Hysteresis prevents the controller from repeatedly reacting
# to small changes around the switching threshold.
#
# Example:
# Switching threshold = 20%
# Rearming threshold = 20% + 5% = 25%
#
# After a threshold-triggered switch, the controller will not
# arm another threshold-triggered switch until the active
# battery reaches the rearming threshold.
DEFAULT_HYSTERESIS_PERCENT = 5.0

# Minimum time between switching attempts.
#
# This uses simulation wall-clock time. It is not a substitute
# for safety interlocks in real battery hardware.
DEFAULT_MIN_SWITCH_INTERVAL_SECONDS = 10.0

# Small tolerance for floating-point percentage comparisons.
SOC_TOLERANCE = 1e-9


# ============================================================
# 2. DUAL-BATTERY MANAGER
# ============================================================

class BatteryManager:
    """
    Coordinate two simulated Battery objects.

    Parameters
    ----------
    battery_a:
        First Battery instance from battery.py.

    battery_b:
        Second Battery instance from battery.py.

    switch_threshold_percent:
        State-of-charge percentage that triggers a switch.

    hysteresis_percent:
        Additional percentage above the switching threshold
        required to rearm threshold-triggered switching.

    min_switch_interval_seconds:
        Minimum wall-clock time between switching attempts.

    initial_active_battery_id:
        Optional initial battery identifier: "A" or "B".

    Notes
    -----
    The manager does not create or modify battery chemistry,
    calculate electrochemical limits, or operate real hardware.
    """

    def __init__(
        self,
        battery_a,
        battery_b,
        switch_threshold_percent=DEFAULT_SWITCH_THRESHOLD,
        hysteresis_percent=DEFAULT_HYSTERESIS_PERCENT,
        min_switch_interval_seconds=(
            DEFAULT_MIN_SWITCH_INTERVAL_SECONDS
        ),
        initial_active_battery_id=None,
    ):

        # ----------------------------------------------------
        # Store the two battery objects.
        # ----------------------------------------------------

        self.batteries = {
            "A": battery_a,
            "B": battery_b,
        }

        # ----------------------------------------------------
        # Validate the switching configuration.
        # ----------------------------------------------------

        self.switch_threshold_percent = float(
            switch_threshold_percent
        )

        self.hysteresis_percent = float(hysteresis_percent)

        self.min_switch_interval_seconds = float(
            min_switch_interval_seconds
        )

        if not 0.0 <= self.switch_threshold_percent <= 100.0:
            raise ValueError(
                "Switch threshold must be between 0 and 100."
            )

        if not 0.0 <= self.hysteresis_percent <= 100.0:
            raise ValueError(
                "Hysteresis must be between 0 and 100."
            )

        if self.min_switch_interval_seconds < 0.0:
            raise ValueError(
                "Minimum switching interval cannot be negative."
            )

        # The rearming threshold is the switching threshold
        # plus the hysteresis margin, capped at 100%.
        self.rearming_threshold_percent = min(
            100.0,
            self.switch_threshold_percent
            + self.hysteresis_percent,
        )

        # ----------------------------------------------------
        # Controller state.
        # ----------------------------------------------------

        # The battery currently selected by the simulation.
        self.active_battery_id = None

        # Last time a switching attempt was made.
        self.last_switch_attempt_time = None

        # Last time a switch completed successfully.
        self.last_successful_switch_time = None

        # The controller begins ready to respond to a threshold.
        self.threshold_armed = True

        # Current high-level controller status.
        self.controller_status = "INITIALIZING"

        # Human-readable explanation of the latest decision.
        self.status_message = "Controller has not initialized."

        # A list of dictionaries describing switching events.
        self.switching_events: List[Dict[str, Any]] = []

        # ----------------------------------------------------
        # Select the initial battery.
        # ----------------------------------------------------

        if initial_active_battery_id is not None:

            initial_id = str(
                initial_active_battery_id
            ).upper()

            if initial_id not in self.batteries:
                raise ValueError(
                    "Initial battery ID must be 'A' or 'B'."
                )

            if self._battery_is_eligible(initial_id):
                self.active_battery_id = initial_id

                self.controller_status = "READY"

                self.status_message = (
                    f"Battery {initial_id} selected initially."
                )

            else:
                # An explicitly requested battery cannot be
                # selected if it is unavailable.
                self.handle_no_available_battery(
                    reason=(
                        f"Requested initial battery {initial_id} "
                        "is not eligible."
                    )
                )

        else:
            # Otherwise, choose the best eligible battery.
            self.select_active_battery()


    # ========================================================
    # 3. INTERNAL HELPER FUNCTIONS
    # ========================================================

    def _get_battery(self, battery_id):
        """
        Return the Battery object associated with an ID.

        Valid IDs are "A" and "B".
        """

        battery_id = str(battery_id).upper()

        if battery_id not in self.batteries:
            raise ValueError(
                "Battery ID must be 'A' or 'B'."
            )

        return self.batteries[battery_id]


    def _alternate_battery_id(self, battery_id):
        """
        Return the ID of the other battery.

        A -> B
        B -> A
        """

        if battery_id == "A":
            return "B"

        if battery_id == "B":
            return "A"

        return None


    def _battery_is_eligible(self, battery_id):
        """
        Check whether a battery can be selected in the simulation.

        Eligibility checks include:
        - The battery ID is valid.
        - The battery is enabled.
        - No recorded faults are present.
        - Its SoC is above its minimum permitted SoC.
        - Its own is_available() method approves availability.

        This is a simplified software check. It is not a
        replacement for real battery safety monitoring.
        """

        if battery_id not in self.batteries:
            return False

        battery = self.batteries[battery_id]

        # A disabled battery cannot be selected.
        if not getattr(battery, "enabled", False):
            return False

        # A battery with recorded faults is not eligible.
        if getattr(battery, "faults", []):
            return False

        # Read the battery's current state of charge.
        soc = getattr(battery, "soc_percent", None)

        if soc is None:
            return False

        # Read the battery's configured minimum SoC.
        minimum_soc = getattr(
            battery,
            "min_soc_percent",
            0.0,
        )

        # Do not select a battery at or below its minimum SoC.
        if soc <= minimum_soc + SOC_TOLERANCE:
            return False

        # Ask the Battery class for its own availability result.
        availability_method = getattr(
            battery,
            "is_available",
            None,
        )

        if callable(availability_method):
            try:
                if not availability_method():
                    return False
            except Exception:
                # A failed availability check must not be
                # treated as proof that the battery is usable.
                return False

        return True


    def _record_event(
        self,
        event_type,
        from_battery=None,
        to_battery=None,
        success=None,
        reason="",
    ):
        """
        Record one controller event.

        The event is stored in memory. Call export_events_to_csv()
        to save the history to a file.
        """

        event = {
            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            ),
            "event_type": event_type,
            "from_battery": from_battery or "",
            "to_battery": to_battery or "",
            "success": (
                "" if success is None else bool(success)
            ),
            "active_battery_id": (
                self.active_battery_id or ""
            ),
            "controller_status": self.controller_status,
            "reason": reason,
        }

        self.switching_events.append(event)

        return event


    def _seconds_since_last_attempt(self):
        """
        Return seconds since the last switching attempt.

        If there has been no attempt, return None.
        """

        if self.last_switch_attempt_time is None:
            return None

        elapsed = (
            datetime.now() - self.last_switch_attempt_time
        ).total_seconds()

        return elapsed


    def _switch_interval_has_elapsed(self):
        """
        Determine whether another switching attempt is allowed.
        """

        elapsed = self._seconds_since_last_attempt()

        # No previous attempt means the interval is satisfied.
        if elapsed is None:
            return True

        return (
            elapsed >= self.min_switch_interval_seconds
        )


    # ========================================================
    # 4. SELECT THE ACTIVE BATTERY
    # ========================================================

    def select_active_battery(self):
        """
        Select an eligible battery.

        If an eligible active battery is already selected,
        retain it instead of switching unnecessarily.

        If no battery is active, select the eligible battery
        with the higher SoC.

        Returns
        -------
        str or None
            "A", "B", or None if neither is eligible.
        """

        # Retain the current battery if it remains eligible.
        if (
            self.active_battery_id is not None
            and self._battery_is_eligible(
                self.active_battery_id
            )
        ):
            self.controller_status = "READY"

            self.status_message = (
                f"Battery {self.active_battery_id} "
                "remains selected."
            )

            return self.active_battery_id

        # Find all batteries that pass the eligibility checks.
        eligible_ids = [
            battery_id
            for battery_id in self.batteries
            if self._battery_is_eligible(battery_id)
        ]

        # There is nothing safe to select if the list is empty.
        if not eligible_ids:
            self.handle_no_available_battery(
                reason="Neither battery is eligible."
            )

            return None

        # Select the eligible battery with the highest SoC.
        selected_id = max(
            eligible_ids,
            key=lambda battery_id: (
                self.batteries[battery_id].soc_percent
            ),
        )

        previous_id = self.active_battery_id

        self.active_battery_id = selected_id

        self.controller_status = "READY"

        self.status_message = (
            f"Battery {selected_id} selected."
        )

        # Record the selection if it changed.
        if previous_id != selected_id:
            self._record_event(
                event_type="BATTERY_SELECTED",
                from_battery=previous_id,
                to_battery=selected_id,
                success=True,
                reason=(
                    "Selected an eligible battery with "
                    "the highest available SoC."
                ),
            )

        return self.active_battery_id


    # ========================================================
    # 5. VALIDATE THE ALTERNATE BATTERY
    # ========================================================

    def validate_alternate_battery(self):
        """
        Check whether the alternate battery can be selected.

        Returns
        -------
        bool
            True if the alternate battery is eligible.
        """

        # Without an active battery, there is no well-defined
        # alternate battery.
        if self.active_battery_id is None:
            self.status_message = (
                "Cannot validate an alternate: "
                "no active battery is selected."
            )

            return False

        alternate_id = self._alternate_battery_id(
            self.active_battery_id
        )

        if alternate_id is None:
            return False

        # Use the same eligibility checks used for selection.
        if not self._battery_is_eligible(alternate_id):

            self.status_message = (
                f"Alternate battery {alternate_id} "
                "is not eligible."
            )

            return False

        self.status_message = (
            f"Alternate battery {alternate_id} "
            "is eligible."
        )

        return True


    # ========================================================
    # 6. CHECK WHETHER SWITCHING IS NECESSARY
    # ========================================================

    def should_switch_battery(self):
        """
        Decide whether the controller should attempt a switch.

        A switch is considered when:
        1. An active battery exists.
        2. Its SoC reaches or falls below the threshold.
        3. The hysteresis trigger is armed.
        4. The minimum switching interval has elapsed.
        5. The alternate battery is eligible.

        Returns
        -------
        bool
            True when a switching attempt should be made.
        """

        # First ensure that a usable battery is selected.
        if self.active_battery_id is None:
            self.select_active_battery()

        if self.active_battery_id is None:
            self.handle_no_available_battery(
                reason="No active battery is available."
            )

            return False

        active_battery = self._get_battery(
            self.active_battery_id
        )

        # If the active battery becomes ineligible, attempt
        # to select the other battery immediately, subject to
        # the simulated switching interval.
        if not self._battery_is_eligible(
            self.active_battery_id
        ):

            self.status_message = (
                f"Active battery {self.active_battery_id} "
                "is no longer eligible."
            )

            if not self._switch_interval_has_elapsed():
                self.controller_status = "SWITCH_COOLDOWN"

                self.status_message += (
                    " Switching interval has not elapsed."
                )

                return False

            if self.validate_alternate_battery():
                return True

            self.handle_no_available_battery(
                reason=(
                    "Active battery is ineligible and "
                    "the alternate is unavailable."
                )
            )

            return False

        # Read the active battery's state of charge.
        active_soc = active_battery.soc_percent

        # Rearm threshold-based switching only after the
        # active battery rises above the rearming threshold.
        if (
            not self.threshold_armed
            and active_soc
            >= self.rearming_threshold_percent
        ):

            self.threshold_armed = True

            self._record_event(
                event_type="THRESHOLD_REARMED",
                from_battery=self.active_battery_id,
                to_battery=self.active_battery_id,
                success=True,
                reason=(
                    "Active battery reached the "
                    "hysteresis rearming threshold."
                ),
            )

        # Do not trigger another threshold-based switch while
        # the threshold is disarmed.
        if not self.threshold_armed:

            self.controller_status = "HYSTERESIS_LOCK"

            self.status_message = (
                "Threshold switching is disarmed until "
                f"SoC reaches {self.rearming_threshold_percent:.1f}%."
            )

            return False

        # Do nothing while the active battery is above the
        # configured switching threshold.
        if (
            active_soc
            > self.switch_threshold_percent
        ):

            self.controller_status = "READY"

            self.status_message = (
                f"Battery {self.active_battery_id} is at "
                f"{active_soc:.1f}% SoC; no switch is needed."
            )

            return False

        # Do not attempt switching repeatedly within the
        # minimum interval.
        if not self._switch_interval_has_elapsed():

            self.controller_status = "SWITCH_COOLDOWN"

            self.status_message = (
                "Switching threshold reached, but the "
                "minimum switching interval has not elapsed."
            )

            return False

        # A threshold does not justify selecting an
        # unavailable alternate battery.
        if not self.validate_alternate_battery():

            self.controller_status = "ALTERNATE_UNAVAILABLE"

            self.status_message = (
                "Switching threshold reached, but the "
                "alternate battery is unavailable."
            )

            return False

        # All required conditions are satisfied.
        self.status_message = (
            "Switching conditions satisfied."
        )

        return True


    # ========================================================
    # 7. SWITCH BATTERIES
    # ========================================================

    def switch_battery(
        self,
        target_battery_id=None,
        simulate_failure=False,
    ):
        """
        Simulate a battery-selection change.

        Parameters
        ----------
        target_battery_id:
            Optional target ID ("A" or "B"). If omitted,
            the alternate battery is used.

        simulate_failure:
            Set True to test the failed-switching path.

        Returns
        -------
        bool
            True if the simulated switch succeeds.

        IMPORTANT
        ---------
        This function changes only the manager's software
        selection. It does not operate physical contactors,
        relays, power electronics, or traction batteries.
        """

        previous_id = self.active_battery_id

        # Determine the target battery.
        if target_battery_id is None:

            if previous_id is None:
                self.select_active_battery()

                previous_id = self.active_battery_id

            if previous_id is None:
                self.handle_no_available_battery(
                    reason=(
                        "Switch failed because no active "
                        "battery is selected."
                    )
                )

                return False

            target_battery_id = self._alternate_battery_id(
                previous_id
            )

        target_battery_id = str(
            target_battery_id
        ).upper()

        # Validate the requested ID.
        if target_battery_id not in self.batteries:

            self.status_message = (
                "Switch rejected: target ID must be A or B."
            )

            self.controller_status = "SWITCH_FAILED"

            self.last_switch_attempt_time = datetime.now()

            self._record_event(
                event_type="SWITCH_FAILED",
                from_battery=previous_id,
                to_battery=target_battery_id,
                success=False,
                reason="Invalid target battery ID.",
            )

            return False

        # Do not switch to the battery that is already active.
        if target_battery_id == previous_id:

            self.status_message = (
                "Switch unnecessary: target is already active."
            )

            return True

        # Enforce the minimum interval between attempts.
        if not self._switch_interval_has_elapsed():

            self.controller_status = "SWITCH_COOLDOWN"

            self.status_message = (
                "Switch rejected because the minimum "
                "switching interval has not elapsed."
            )

            return False

        # Record the attempt time even when the simulated
        # operation fails.
        self.last_switch_attempt_time = datetime.now()

        self.controller_status = "SWITCHING"

        # Validate the target before changing the active ID.
        if not self._battery_is_eligible(target_battery_id):

            self.controller_status = "SWITCH_FAILED"

            self.status_message = (
                f"Switch failed: battery {target_battery_id} "
                "is not eligible."
            )

            self._record_event(
                event_type="SWITCH_FAILED",
                from_battery=previous_id,
                to_battery=target_battery_id,
                success=False,
                reason="Target battery failed eligibility checks.",
            )

            return False

        # This flag is solely for testing failure handling.
        if simulate_failure:

            self.controller_status = "SWITCH_FAILED"

            self.status_message = (
                "Simulated switching failure. "
                "The previous active selection is unchanged."
            )

            self._record_event(
                event_type="SWITCH_FAILED",
                from_battery=previous_id,
                to_battery=target_battery_id,
                success=False,
                reason="Failure deliberately injected for testing.",
            )

            return False

        # ----------------------------------------------------
        # Simulated switch succeeds.
        # ----------------------------------------------------

        self.active_battery_id = target_battery_id

        self.last_successful_switch_time = datetime.now()

        self.controller_status = "READY"

        self.status_message = (
            f"Successfully switched from battery "
            f"{previous_id} to battery {target_battery_id}."
        )

        # Disarm threshold-based switching until the
        # rearming condition is satisfied.
        self.threshold_armed = False

        self._record_event(
            event_type="SWITCH_SUCCESS",
            from_battery=previous_id,
            to_battery=target_battery_id,
            success=True,
            reason="Target battery passed eligibility checks.",
        )

        return True


    # ========================================================
    # 8. HANDLE THE CASE WHERE NO BATTERY IS AVAILABLE
    # ========================================================

    def handle_no_available_battery(self, reason=""):
        """
        Place the simulated controller into an unavailable state.

        No battery is selected when neither battery passes
        the eligibility checks.

        In a real vehicle, a safety-rated system would have
        to manage this condition independently.
        """

        self.active_battery_id = None

        self.controller_status = "NO_AVAILABLE_BATTERY"

        self.status_message = (
            reason or "Neither battery is eligible."
        )

        self._record_event(
            event_type="NO_AVAILABLE_BATTERY",
            from_battery=None,
            to_battery=None,
            success=False,
            reason=self.status_message,
        )

        return None


    # ========================================================
    # 9. UPDATE THE CONTROLLER
    # ========================================================

    def update(self):
        """
        Run one controller decision cycle.

        Suggested simulation sequence:
            1. Update the battery SoC values.
            2. Call manager.update().
            3. Inspect the controller status.
            4. Record or display the resulting state.

        Returns
        -------
        dict
            A snapshot of the current controller state.
        """

        # If the active battery has become ineligible, attempt
        # to switch to an eligible alternate if allowed.
        if (
            self.active_battery_id is not None
            and not self._battery_is_eligible(
                self.active_battery_id
            )
        ):

            if self._battery_is_eligible(
                self._alternate_battery_id(
                    self.active_battery_id
                )
            ):

                if self._switch_interval_has_elapsed():

                    self.switch_battery()

                else:

                    self.controller_status = "SWITCH_COOLDOWN"

                    self.status_message = (
                        "Active battery is ineligible, but "
                        "the switching interval has not elapsed."
                    )

            else:

                self.handle_no_available_battery(
                    reason=(
                        "The active battery and its alternate "
                        "are both ineligible."
                    )
                )

            return self.get_controller_state()

        # If there is no active selection, try to select one.
        if self.active_battery_id is None:

            self.select_active_battery()

            if self.active_battery_id is None:
                return self.get_controller_state()

        # Evaluate the threshold and attempt a switch if
        # all configured conditions are satisfied.
        if self.should_switch_battery():

            self.switch_battery()

        return self.get_controller_state()


    # ========================================================
    # 10. RETURN THE CURRENT CONTROLLER STATE
    # ========================================================

    def get_controller_state(self):
        """
        Return a dictionary describing the current state.

        This dictionary can later be used by a dashboard,
        simulator, or data logger.
        """

        active_soc = None

        if self.active_battery_id is not None:

            active_soc = self._get_battery(
                self.active_battery_id
            ).soc_percent

        # Summarize both batteries.
        battery_states = {}

        for battery_id, battery in self.batteries.items():

            battery_states[battery_id] = {
                "soc_percent": battery.soc_percent,
                "eligible": self._battery_is_eligible(
                    battery_id
                ),
                "enabled": getattr(
                    battery,
                    "enabled",
                    False,
                ),
                "faults": list(
                    getattr(battery, "faults", [])
                ),
            }

        return {
            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            ),
            "active_battery_id": self.active_battery_id,
            "active_battery_soc_percent": active_soc,
            "switch_threshold_percent": (
                self.switch_threshold_percent
            ),
            "rearming_threshold_percent": (
                self.rearming_threshold_percent
            ),
            "threshold_armed": self.threshold_armed,
            "controller_status": self.controller_status,
            "status_message": self.status_message,
            "batteries": battery_states,
            "switching_event_count": len(
                self.switching_events
            ),
        }


    # ========================================================
    # 11. DISPLAY A STATUS REPORT
    # ========================================================

    def print_status(self):
        """
        Print the controller state in a readable format.
        """

        state = self.get_controller_state()

        print("\n" + "=" * 60)
        print("FLUXXWAVE — DUAL-BATTERY MANAGER")
        print("=" * 60)

        print(
            f"Active battery       : "
            f"{state['active_battery_id'] or 'NONE'}"
        )

        print(
            f"Active battery SoC   : "
            f"{state['active_battery_soc_percent']}"
        )

        print(
            f"Switch threshold     : "
            f"{state['switch_threshold_percent']:.1f}%"
        )

        print(
            f"Rearming threshold   : "
            f"{state['rearming_threshold_percent']:.1f}%"
        )

        print(
            f"Threshold armed      : "
            f"{state['threshold_armed']}"
        )

        print(
            f"Controller status    : "
            f"{state['controller_status']}"
        )

        print(
            f"Status message       : "
            f"{state['status_message']}"
        )

        print("\nBATTERY DETAILS")

        for battery_id, battery_state in (
            state["batteries"].items()
        ):

            print(f"\nBattery {battery_id}")

            print(
                f"  SoC       : "
                f"{battery_state['soc_percent']:.1f}%"
            )

            print(
                f"  Eligible  : "
                f"{battery_state['eligible']}"
            )

            print(
                f"  Enabled   : "
                f"{battery_state['enabled']}"
            )

            print(
                f"  Faults    : "
                f"{battery_state['faults']}"
            )

        print(
            f"\nTotal logged events  : "
            f"{state['switching_event_count']}"
        )

        print("=" * 60)


    # ========================================================
    # 12. EXPORT SWITCHING HISTORY TO CSV
    # ========================================================

    def export_events_to_csv(
        self,
        filename="data/battery_switching_events.csv",
    ):
        """
        Save the switching event history as a CSV file.

        The destination directory is created if necessary.

        Returns
        -------
        str
            The output file path.
        """

        output_path = Path(filename)

        # Create the parent directory when one is specified.
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Define a consistent column order.
        fieldnames = [
            "timestamp",
            "event_type",
            "from_battery",
            "to_battery",
            "success",
            "active_battery_id",
            "controller_status",
            "reason",
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
                self.switching_events
            )

        print(
            f"Switching history exported to: {output_path}"
        )

        return str(output_path)


# ============================================================
# 13. DEMONSTRATION
# ============================================================

def run_demo():
    """
    Demonstrate the manager using simulated batteries.

    This function expects battery.py to provide:
        create_battery_a()
        create_battery_b()

    It does not connect to physical batteries.
    """

    # Import the existing simulated Battery factories.
    from battery import (
        create_battery_a,
        create_battery_b,
    )

    # Create two independent simulated battery objects.
    battery_a = create_battery_a()
    battery_b = create_battery_b()

    # Configure the dual-battery manager.
    manager = BatteryManager(
        battery_a=battery_a,
        battery_b=battery_b,
        switch_threshold_percent=20.0,
        hysteresis_percent=5.0,
        min_switch_interval_seconds=0.0,
        initial_active_battery_id="A",
    )

    # --------------------------------------------------------
    # DEMO 1: Display the initial configuration.
    # --------------------------------------------------------

    print("\nDEMO 1: INITIAL BATTERY STATE")

    manager.print_status()

    # --------------------------------------------------------
    # DEMO 2: Simulate battery A reaching the threshold.
    # --------------------------------------------------------

    print("\nDEMO 2: SWITCH AT THE 20% THRESHOLD")

    # Update only the simulated SoC.
    # No real battery is charged or discharged here.
    battery_a.update_soc(20.0)

    # The alternate battery should be checked before switching.
    print(
        "Alternate eligible:",
        manager.validate_alternate_battery(),
    )

    # Run one controller cycle.
    manager.update()

    manager.print_status()

    # --------------------------------------------------------
    # DEMO 3: Test the failed-switching path.
    # --------------------------------------------------------

    print("\nDEMO 3: SIMULATED SWITCHING FAILURE")

    # Attempt to switch back while deliberately injecting
    # a simulated failure.
    #
    # The zero-second interval is configured for this demo.
    # The threshold logic itself is not being bypassed here:
    # this is a direct test of switch_battery().
    target_id = manager._alternate_battery_id(
        manager.active_battery_id
    )

    if target_id is not None:

        result = manager.switch_battery(
            target_battery_id=target_id,
            simulate_failure=True,
        )

        print("Switch successful:", result)

        manager.print_status()

    # --------------------------------------------------------
    # DEMO 4: Test the no-available-battery condition.
    # --------------------------------------------------------

    print("\nDEMO 4: NO ELIGIBLE BATTERIES")

    # Make both batteries ineligible for this simulation.
    battery_a.disable()
    battery_b.disable()

    manager.update()

    manager.print_status()

    # --------------------------------------------------------
    # DEMO 5: Export the event log.
    # --------------------------------------------------------

    print("\nDEMO 5: EXPORT SWITCHING HISTORY")

    manager.export_events_to_csv(
        "data/battery_switching_events.csv"
    )

    print("\nDemo completed.")


# ============================================================
# 14. SCRIPT ENTRY POINT
# ============================================================

# This block executes only when this file is run directly.
# Importing BatteryManager from another module will not run
# the demonstration automatically.

if __name__ == "__main__":
    run_demo()
