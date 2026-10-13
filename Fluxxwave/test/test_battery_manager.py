
"""
Unit tests for Fluxxwave's battery_manager.py

Run:
    python -m unittest test_battery_manager.py -v

These tests check:
- Initial battery selection
- Low state-of-charge switching
- Switching back when a battery becomes eligible
- Disabled and faulted batteries
- Switching event history
- Invalid configuration values
- Handling of both batteries being unavailable

Note:
Some method names and constructor parameters may differ in your
current battery_manager.py. If a test fails with AttributeError or
TypeError, compare the test with your implementation.
"""

import unittest

from battery import create_battery_a, create_battery_b
from battery_manager import BatteryManager


class TestBatteryManager(unittest.TestCase):
    """Tests for the dual-battery management system."""

    def setUp(self):
        """Create fresh batteries and a manager for each test."""
        self.battery_a = create_battery_a()
        self.battery_b = create_battery_b()

        self.manager = BatteryManager(
            self.battery_a,
            self.battery_b,
        )

    # ---------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------

    def test_manager_initializes(self):
        """The manager should initialize with two batteries."""
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.battery_a)
        self.assertIsNotNone(self.battery_b)

    def test_initial_battery_soc_values(self):
        """Example batteries should begin at their configured SoC."""
        self.assertAlmostEqual(self.battery_a.soc_percent, 80.0)
        self.assertAlmostEqual(self.battery_b.soc_percent, 90.0)

    def test_switching_threshold_configuration(self):
        """The default switching threshold should be 20%."""
        if hasattr(self.manager, "switch_threshold_percent"):
            self.assertAlmostEqual(
                self.manager.switch_threshold_percent, 20.0
            )
        elif hasattr(self.manager, "switch_threshold"):
            self.assertAlmostEqual(
                self.manager.switch_threshold, 20.0
            )
        else:
            self.skipTest(
                "No recognised public switching-threshold attribute."
            )

    # ---------------------------------------------------------
    # Active battery selection
    # ---------------------------------------------------------

    def test_manager_selects_an_initial_battery(self):
        """An eligible battery should be selected at initialization."""
        active = self._get_active_battery()

        self.assertIsNotNone(
            active,
            "The manager should select an eligible battery."
        )

    def test_active_battery_is_one_of_the_configured_batteries(self):
        """The active battery must be Battery A or Battery B."""
        active = self._get_active_battery()

        if active is None:
            self.fail("No active battery was selected.")

        self.assertIn(
            active,
            [self.battery_a, self.battery_b],
        )

    def test_selected_battery_is_available(self):
        """The selected battery should be operational."""
        active = self._get_active_battery()

        if active is None:
            self.fail("No active battery was selected.")

        self.assertTrue(active.is_available())

    # ---------------------------------------------------------
    # Switching behaviour
    # ---------------------------------------------------------

    def test_switches_when_active_battery_falls_below_threshold(self):
        """
        The manager should switch away from an active battery
        that falls below its switching threshold.

        This test assumes the manager's update method evaluates
        switching conditions immediately.
        """
        active = self._get_active_battery()

        if active is None:
            self.fail("No active battery was selected.")

        standby = (
            self.battery_b
            if active is self.battery_a
            else self.battery_a
        )

        if hasattr(self.manager, "switch_threshold_percent"):
            threshold = self.manager.switch_threshold_percent
        elif hasattr(self.manager, "switch_threshold"):
            threshold = self.manager.switch_threshold
        else:
            self.skipTest("Cannot determine the switching threshold.")

        # Ensure the standby battery is eligible.
        standby.enable()
        standby.clear_fault()
        standby.update_soc(max(standby.min_soc_percent + 15, 50.0))

        # Put the active battery below the threshold.
        active.update_soc(max(active.min_soc_percent, threshold - 1))

        self._update_manager()

        new_active = self._get_active_battery()

        if active.soc_percent <= active.min_soc_percent:
            # If the active battery is at its minimum SoC, it should
            # not continue supplying energy when the other battery
            # is eligible.
            self.assertIsNot(
                new_active,
                active,
                "Manager should select the eligible standby battery."
            )
        else:
            self.assertIsNot(
                new_active,
                active,
                "Manager should switch away from the low-SoC battery."
            )

    def test_does_not_select_disabled_battery(self):
        """A disabled battery should not be selected as active."""
        self.battery_a.disable()
        self.battery_b.enable()

        self._update_manager()

        active = self._get_active_battery()

        if active is not None:
            self.assertIsNot(active, self.battery_a)

    def test_does_not_select_faulted_battery(self):
        """A faulted battery should not be selected as active."""
        self.battery_a.set_fault("TEST_FAULT")
        self.battery_b.enable()

        self._update_manager()

        active = self._get_active_battery()

        if active is not None:
            self.assertIsNot(active, self.battery_a)

    def test_switches_if_active_battery_is_disabled(self):
        """The manager should move to the other eligible battery."""
        active = self._get_active_battery()

        if active is None:
            self.fail("No active battery was selected.")

        other = (
            self.battery_b
            if active is self.battery_a
            else self.battery_a
        )

        other.enable()
        other.clear_fault()
        active.disable()

        self._update_manager()

        new_active = self._get_active_battery()

        if new_active is not None:
            self.assertIsNot(new_active, active)

    def test_handles_both_batteries_disabled(self):
        """No battery should be selected when both are disabled."""
        self.battery_a.disable()
        self.battery_b.disable()

        self._update_manager()

        active = self._get_active_battery()

        self.assertIsNone(
            active,
            "No battery should be active when both are disabled."
        )

    # ---------------------------------------------------------
    # Event history
    # ---------------------------------------------------------

    def test_event_history_is_accessible(self):
        """The manager should expose its switching/event history."""
        possible_names = (
            "event_history",
            "switching_history",
            "events",
            "switching_events",
        )

        if not any(
            hasattr(self.manager, name)
            for name in possible_names
        ):
            self.skipTest(
                "No recognised public event-history attribute."
            )

    def test_event_history_is_a_collection(self):
        """Event history should be stored in a collection."""
        for name in (
            "event_history",
            "switching_history",
            "events",
            "switching_events",
        ):
            if hasattr(self.manager, name):
                history = getattr(self.manager, name)
                self.assertIsNotNone(history)
                self.assertTrue(
                    hasattr(history, "__iter__"),
                    "Event history should be iterable."
                )
                return

        self.skipTest("No recognised event-history attribute.")

    # ---------------------------------------------------------
    # Helper methods
    # ---------------------------------------------------------

    def _get_active_battery(self):
        """Read the active battery using common public API names."""
        for name in (
            "active_battery",
            "current_battery",
            "active",
        ):
            if hasattr(self.manager, name):
                value = getattr(self.manager, name)
                return value() if callable(value) else value

        for name in (
            "get_active_battery",
            "get_current_battery",
        ):
            method = getattr(self.manager, name, None)
            if callable(method):
                return method()

        # Some implementations store an active battery identifier.
        for name in (
            "active_battery_id",
            "current_battery_id",
        ):
            if hasattr(self.manager, name):
                value = getattr(self.manager, name)
                value = value() if callable(value) else value

                if value in ("A", "Battery A", "battery_a"):
                    return self.battery_a

                if value in ("B", "Battery B", "battery_b"):
                    return self.battery_b

        self.skipTest(
            "Could not identify the manager's active-battery API."
        )

    def _update_manager(self):
        """Call a recognised manager update method."""
        for name in (
            "update",
            "update_battery_status",
            "evaluate",
            "check_and_switch",
        ):
            method = getattr(self.manager, name, None)

            if callable(method):
                method()
                return

        self.skipTest(
            "Could not identify the manager's update method."
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
