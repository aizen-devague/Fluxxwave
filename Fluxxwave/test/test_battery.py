
"""
Fluxxwave EV — Battery Unit Tests
==================================

Tests:
1. Battery creation and initial state.
2. Stored and available energy calculations.
3. State-of-charge updates.
4. Battery discharge and charge behaviour.
5. Charge/discharge power limits.
6. Temperature and fault handling.
7. Enable/disable behaviour.
8. Battery status and availability.

Run:
    python -m unittest test_battery.py -v

These tests validate the software battery model, not a physical
battery or battery-management system.
"""

import unittest

from battery import (
    Battery,
    create_battery_a,
    create_battery_b,
)


class TestBatteryInitialization(unittest.TestCase):
    """Test battery construction and initial state."""

    def setUp(self):
        self.battery = create_battery_a()

    def test_factory_creates_battery(self):
        self.assertIsInstance(self.battery, Battery)

    def test_initial_capacity(self):
        self.assertAlmostEqual(
            self.battery.capacity_kwh,
            2.0,
        )

    def test_initial_state_of_charge(self):
        self.assertAlmostEqual(
            self.battery.soc_percent,
            80.0,
        )

    def test_initial_stored_energy(self):
        # 2.0 kWh × 80% = 1.6 kWh
        self.assertAlmostEqual(
            self.battery.stored_energy_kwh,
            1.6,
            places=6,
        )

    def test_battery_b_initial_state(self):
        battery_b = create_battery_b()

        self.assertIsInstance(battery_b, Battery)
        self.assertAlmostEqual(battery_b.soc_percent, 90.0)
        self.assertAlmostEqual(battery_b.capacity_kwh, 2.0)


class TestBatteryEnergyCalculations(unittest.TestCase):
    """Test stored, available, and remaining energy."""

    def setUp(self):
        self.battery = create_battery_a()

    def test_stored_energy_in_wh(self):
        # 1.6 kWh = 1600 Wh
        self.assertAlmostEqual(
            self.battery.stored_energy_wh,
            1600.0,
            places=6,
        )

    def test_available_energy_above_minimum_soc(self):
        # At 80% SoC with a 20% minimum:
        # (80% - 20%) × 2 kWh = 1.2 kWh
        self.assertAlmostEqual(
            self.battery.available_energy_kwh,
            1.2,
            places=6,
        )

    def test_remaining_charge_capacity(self):
        # At 80% SoC, 20% capacity remains.
        self.assertAlmostEqual(
            self.battery.remaining_charge_capacity_kwh,
            0.4,
            places=6,
        )

    def test_available_energy_after_discharge(self):
        self.battery.consume_energy(0.3)

        # Stored energy becomes 1.3 kWh.
        # Available energy above the 20% minimum is 0.9 kWh.
        self.assertAlmostEqual(
            self.battery.stored_energy_kwh,
            1.3,
            places=6,
        )

        self.assertAlmostEqual(
            self.battery.available_energy_kwh,
            0.9,
            places=6,
        )


class TestBatteryStateOfCharge(unittest.TestCase):
    """Test direct SoC updates."""

    def setUp(self):
        self.battery = create_battery_a()

    def test_update_soc(self):
        self.battery.update_soc(60.0)

        self.assertAlmostEqual(
            self.battery.soc_percent,
            60.0,
        )

    def test_update_soc_changes_stored_energy(self):
        self.battery.update_soc(50.0)

        self.assertAlmostEqual(
            self.battery.stored_energy_kwh,
            1.0,
            places=6,
        )

    def test_invalid_soc_above_100_is_rejected(self):
        with self.assertRaises((ValueError, TypeError)):
            self.battery.update_soc(101.0)

    def test_invalid_negative_soc_is_rejected(self):
        with self.assertRaises((ValueError, TypeError)):
            self.battery.update_soc(-1.0)


class TestBatteryDischarging(unittest.TestCase):
    """Test energy consumption and discharge constraints."""

    def setUp(self):
        self.battery = create_battery_a()

    def test_discharge_reduces_soc(self):
        # 0.3 kWh from a 2 kWh battery is 15 percentage points.
        self.battery.consume_energy(0.3)

        self.assertAlmostEqual(
            self.battery.soc_percent,
            65.0,
            places=6,
        )

    def test_discharge_updates_energy_counter(self):
        self.battery.consume_energy(0.3)

        self.assertAlmostEqual(
            self.battery.total_energy_consumed_kwh,
            0.3,
            places=6,
        )

    def test_discharge_to_minimum_soc(self):
        # Initial SoC = 80%; minimum = 20%.
        # 60% of 2 kWh = 1.2 kWh available.
        self.battery.consume_energy(1.2)

        self.assertAlmostEqual(
            self.battery.soc_percent,
            20.0,
            places=6,
        )

    def test_discharge_beyond_available_energy_is_rejected(self):
        with self.assertRaises((ValueError, RuntimeError)):
            self.battery.consume_energy(1.3)

    def test_negative_discharge_is_rejected(self):
        with self.assertRaises((ValueError, TypeError)):
            self.battery.consume_energy(-0.1)

    def test_zero_discharge_does_not_change_soc(self):
        original_soc = self.battery.soc_percent
        self.battery.consume_energy(0.0)

        self.assertAlmostEqual(
            self.battery.soc_percent,
            original_soc,
        )

    def test_discharge_power_limit(self):
        # 1 kWh delivered over 1 second requires 3.6 MW,
        # which exceeds the example battery's discharge power limit.
        with self.assertRaises((ValueError, RuntimeError)):
            self.battery.consume_energy(
                1.0,
                duration_s=1.0,
            )


class TestBatteryCharging(unittest.TestCase):
    """Test energy input and charging efficiency."""

    def setUp(self):
        self.battery = create_battery_a()

    def test_charging_increases_soc(self):
        initial_soc = self.battery.soc_percent

        self.battery.add_energy(
            0.2,
            apply_charge_efficiency=False,
        )

        self.assertGreater(
            self.battery.soc_percent,
            initial_soc,
        )

    def test_charging_efficiency_is_applied(self):
        battery = create_battery_a()
        initial_energy = battery.stored_energy_kwh

        # At 95% efficiency, 0.2 kWh input stores 0.19 kWh.
        battery.add_energy(
            0.2,
            apply_charge_efficiency=True,
        )

        stored_delta = (
            battery.stored_energy_kwh - initial_energy
        )

        self.assertAlmostEqual(
            stored_delta,
            0.19,
            places=6,
        )

    def test_charging_updates_energy_counter(self):
        self.battery.add_energy(
            0.2,
            apply_charge_efficiency=False,
        )

        self.assertAlmostEqual(
            self.battery.total_energy_added_kwh,
            0.2,
            places=6,
        )

    def test_negative_charging_input_is_rejected(self):
        with self.assertRaises((ValueError, TypeError)):
            self.battery.add_energy(-0.1)

    def test_charging_does_not_exceed_capacity(self):
        # This input is larger than the battery's remaining capacity.
        self.battery.add_energy(
            10.0,
            apply_charge_efficiency=False,
        )

        self.assertLessEqual(
            self.battery.stored_energy_kwh,
            self.battery.capacity_kwh,
        )

    def test_charging_power_limit(self):
        # 1 kWh input over one second exceeds the example
        # battery's maximum charging power.
        with self.assertRaises((ValueError, RuntimeError)):
            self.battery.add_energy(
                1.0,
                duration_s=1.0,
            )


class TestBatteryTemperature(unittest.TestCase):
    """Test temperature updates and status checks."""

    def setUp(self):
        self.battery = create_battery_a()

    def test_update_temperature(self):
        self.battery.update_temperature(30.0)

        self.assertAlmostEqual(
            self.battery.temperature_c,
            30.0,
        )

    def test_overtemperature_affects_availability(self):
        self.battery.update_temperature(
            self.battery.max_temperature_c + 5.0
        )

        self.assertFalse(self.battery.is_available())

    def test_temperature_returns_to_normal(self):
        self.battery.update_temperature(
            self.battery.max_temperature_c + 5.0
        )

        self.battery.update_temperature(25.0)

        self.assertTrue(self.battery.is_available())


class TestBatteryFaults(unittest.TestCase):
    """Test manual fault handling."""

    def setUp(self):
        self.battery = create_battery_a()

    def test_setting_fault(self):
        self.battery.set_fault("TEST_FAULT")

        self.assertIn(
            "TEST_FAULT",
            self.battery.faults,
        )

    def test_fault_makes_battery_unavailable(self):
        self.battery.set_fault("TEST_FAULT")

        self.assertFalse(
            self.battery.is_available()
        )

    def test_clearing_fault(self):
        self.battery.set_fault("TEST_FAULT")
        self.battery.clear_fault("TEST_FAULT")

        self.assertNotIn(
            "TEST_FAULT",
            self.battery.faults,
        )

    def test_cleared_fault_restores_availability(self):
        self.battery.set_fault("TEST_FAULT")
        self.battery.clear_fault("TEST_FAULT")

        self.assertTrue(
            self.battery.is_available()
        )


class TestBatteryEnableDisable(unittest.TestCase):
    """Test enable and disable operations."""

    def setUp(self):
        self.battery = create_battery_a()

    def test_disable_battery(self):
        self.battery.disable()

        self.assertFalse(self.battery.enabled)

    def test_disabled_battery_is_unavailable(self):
        self.battery.disable()

        self.assertFalse(self.battery.is_available())

    def test_enable_battery(self):
        self.battery.disable()
        self.battery.enable()

        self.assertTrue(self.battery.enabled)

    def test_enabled_battery_can_be_available(self):
        self.battery.disable()
        self.battery.enable()

        self.assertTrue(self.battery.is_available())


class TestBatteryStatus(unittest.TestCase):
    """Test the reported battery status."""

    def setUp(self):
        self.battery = create_battery_a()

    def test_get_state_returns_dictionary(self):
        state = self.battery.get_state()

        self.assertIsInstance(state, dict)

    def test_get_state_contains_soc(self):
        state = self.battery.get_state()

        self.assertTrue(
            any("soc" in key.lower() for key in state)
        )

    def test_voltage_estimate_is_non_negative(self):
        self.assertGreaterEqual(
            self.battery.estimated_voltage_v,
            0.0,
        )

    def test_status_check_returns_result(self):
        status = self.battery.check_battery_status()

        self.assertIsNotNone(status)


if __name__ == "__main__":
    unittest.main(verbosity=2)
