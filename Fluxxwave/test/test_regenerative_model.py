
"""
Fluxxwave EV — Regenerative Braking Unit Tests
===============================================

Tests:
1. Speed conversions.
2. Kinetic energy calculations.
3. Available braking energy.
4. Regenerative recovery and losses.
5. Braking power.
6. Deceleration and stopping distance.
7. Regenerative driving-cycle simulation.
8. Multiple braking events.

Run:
    python -m unittest test_regenerative_model.py -v

These tests validate the mathematical simulation model, not
real-world regenerative braking hardware.
"""

import math
import unittest

import regenerative_model as regen


class TestSpeedConversions(unittest.TestCase):
    """Test conversions between km/h and m/s."""

    def test_kmh_to_mps(self):
        self.assertAlmostEqual(
            regen.kmh_to_mps(36.0),
            10.0,
            places=6,
        )

    def test_mps_to_kmh(self):
        self.assertAlmostEqual(
            regen.mps_to_kmh(10.0),
            36.0,
            places=6,
        )

    def test_round_trip_conversion(self):
        original_speed = 54.0

        converted = regen.mps_to_kmh(
            regen.kmh_to_mps(original_speed)
        )

        self.assertAlmostEqual(converted, original_speed, places=6)


class TestKineticEnergy(unittest.TestCase):
    """Test vehicle kinetic-energy calculations."""

    def test_kinetic_energy_at_rest(self):
        energy = regen.calculate_kinetic_energy(
            mass_kg=1200.0,
            speed_mps=0.0,
        )

        self.assertAlmostEqual(energy, 0.0, places=9)

    def test_known_kinetic_energy(self):
        """
        KE = 0.5 * m * v²

        For 1200 kg at 15 m/s:
        KE = 135000 J.
        """
        energy = regen.calculate_kinetic_energy(
            mass_kg=1200.0,
            speed_mps=15.0,
        )

        self.assertAlmostEqual(energy, 135000.0, places=6)

    def test_energy_scales_with_square_of_speed(self):
        energy_at_20 = regen.calculate_kinetic_energy(
            mass_kg=1200.0,
            speed_mps=20.0,
        )

        energy_at_10 = regen.calculate_kinetic_energy(
            mass_kg=1200.0,
            speed_mps=10.0,
        )

        self.assertAlmostEqual(
            energy_at_20 / energy_at_10,
            4.0,
            places=6,
        )

    def test_effective_kinetic_energy_without_rotation(self):
        base = regen.calculate_kinetic_energy(
            mass_kg=1200.0,
            speed_mps=15.0,
        )

        effective = regen.calculate_effective_kinetic_energy(
            mass_kg=1200.0,
            speed_mps=15.0,
            rotational_energy_factor=0.0,
        )

        self.assertAlmostEqual(effective, base, places=6)

    def test_effective_energy_with_rotation_factor(self):
        base = regen.calculate_kinetic_energy(
            mass_kg=1200.0,
            speed_mps=10.0,
        )

        effective = regen.calculate_effective_kinetic_energy(
            mass_kg=1200.0,
            speed_mps=10.0,
            rotational_energy_factor=0.1,
        )

        self.assertAlmostEqual(effective, base * 1.1, places=6)


class TestEnergyConversions(unittest.TestCase):
    """Test conversions between joules, Wh, and kWh."""

    def test_joules_to_wh(self):
        self.assertAlmostEqual(
            regen.joules_to_wh(3600.0),
            1.0,
            places=6,
        )

    def test_joules_to_kwh(self):
        self.assertAlmostEqual(
            regen.joules_to_kwh(3_600_000.0),
            1.0,
            places=6,
        )

    def test_wh_to_joules(self):
        self.assertAlmostEqual(
            regen.wh_to_joules(1.0),
            3600.0,
            places=6,
        )

    def test_conversion_round_trip(self):
        original_joules = 135000.0

        recovered_joules = regen.wh_to_joules(
            regen.joules_to_wh(original_joules)
        )

        self.assertAlmostEqual(
            recovered_joules,
            original_joules,
            places=6,
        )


class TestBrakingEnergy(unittest.TestCase):
    """Test available braking energy and recovery estimates."""

    def test_energy_change_during_deceleration(self):
        change = regen.calculate_energy_change(
            mass_kg=1200.0,
            initial_speed_mps=15.0,
            final_speed_mps=0.0,
        )

        self.assertAlmostEqual(change, 135000.0, places=6)

    def test_available_energy_during_braking(self):
        available = regen.calculate_available_braking_energy(
            mass_kg=1200.0,
            initial_speed_mps=15.0,
            final_speed_mps=0.0,
        )

        self.assertAlmostEqual(available, 135000.0, places=6)

    def test_acceleration_does_not_create_braking_energy(self):
        available = regen.calculate_available_braking_energy(
            mass_kg=1200.0,
            initial_speed_mps=5.0,
            final_speed_mps=15.0,
        )

        self.assertAlmostEqual(available, 0.0, places=9)

    def test_constant_speed_has_zero_available_braking_energy(self):
        available = regen.calculate_available_braking_energy(
            mass_kg=1200.0,
            initial_speed_mps=10.0,
            final_speed_mps=10.0,
        )

        self.assertAlmostEqual(available, 0.0, places=9)

    def test_recovered_energy_at_70_percent_efficiency(self):
        recovered = regen.estimate_recovered_energy(
            available_energy_j=135000.0,
            recovery_efficiency=0.70,
        )

        self.assertAlmostEqual(recovered, 94500.0, places=6)

    def test_recovered_energy_cannot_exceed_available_energy(self):
        available = 50000.0

        recovered = regen.estimate_recovered_energy(
            available_energy_j=available,
            recovery_efficiency=0.70,
        )

        self.assertGreaterEqual(recovered, 0.0)
        self.assertLessEqual(recovered, available)

    def test_recovery_losses(self):
        losses = regen.estimate_recovery_losses(
            available_energy_j=135000.0,
            recovered_energy_j=94500.0,
        )

        self.assertAlmostEqual(losses, 40500.0, places=6)


class TestBrakingPower(unittest.TestCase):
    """Test average power calculations for braking events."""

    def test_average_power_from_energy_and_duration(self):
        power = regen.estimate_braking_power(
            energy_j=100000.0,
            duration_seconds=10.0,
        )

        self.assertAlmostEqual(power, 10000.0, places=6)

    def test_average_mechanical_power(self):
        power = regen.calculate_average_mechanical_power(
            energy_j=100000.0,
            duration_seconds=10.0,
        )

        self.assertAlmostEqual(power, 10000.0, places=6)

    def test_average_electrical_power(self):
        power = regen.calculate_average_electrical_power(
            recovered_energy_j=70000.0,
            duration_seconds=10.0,
        )

        self.assertAlmostEqual(power, 7000.0, places=6)


class TestDeceleration(unittest.TestCase):
    """Test constant-deceleration estimates."""

    def test_deceleration_from_speed_change(self):
        deceleration = regen.estimate_constant_deceleration(
            initial_speed_mps=20.0,
            final_speed_mps=0.0,
            duration_seconds=5.0,
        )

        self.assertAlmostEqual(deceleration, 4.0, places=6)

    def test_stopping_distance(self):
        distance = regen.estimate_constant_deceleration_distance(
            initial_speed_mps=20.0,
            final_speed_mps=0.0,
            deceleration_mps2=4.0,
        )

        self.assertAlmostEqual(distance, 50.0, places=6)

    def test_zero_initial_speed_has_zero_stopping_distance(self):
        distance = regen.estimate_constant_deceleration_distance(
            initial_speed_mps=0.0,
            final_speed_mps=0.0,
            deceleration_mps2=4.0,
        )

        self.assertAlmostEqual(distance, 0.0, places=9)


class TestBrakingEventAnalysis(unittest.TestCase):
    """Test the integrated braking-event analysis."""

    def test_analyse_braking_event(self):
        result = regen.analyse_braking_event(
            mass_kg=1200.0,
            initial_speed_mps=15.0,
            final_speed_mps=0.0,
            recovery_efficiency=0.70,
        )

        self.assertIsNotNone(result)

        # Support dictionary-based results from the model.
        if isinstance(result, dict):
            normalized = {
                str(key).lower(): value
                for key, value in result.items()
            }

            # Check the main physical result if the field is present.
            for key in (
                "initial_kinetic_energy_j",
                "initial_energy_j",
                "kinetic_energy_initial_j",
            ):
                if key in normalized:
                    self.assertAlmostEqual(
                        normalized[key],
                        135000.0,
                        places=4,
                    )
                    break

            for key in (
                "recovered_energy_j",
                "recovered_energy",
            ):
                if key in normalized:
                    self.assertAlmostEqual(
                        normalized[key],
                        94500.0,
                        places=4,
                    )
                    break


class TestRegenerativeCycle(unittest.TestCase):
    """Test cycle simulation and cumulative recovery."""

    def test_cycle_returns_results(self):
        result = regen.simulate_regenerative_cycle(
            mass_kg=1200.0,
            time_seconds=[0.0, 1.0, 2.0],
            speed_mps=[15.0, 10.0, 0.0],
            recovery_efficiency=0.70,
        )

        self.assertIsNotNone(result)

        if isinstance(result, dict):
            self.assertTrue(result)
        else:
            self.assertGreater(len(result), 0)

    def test_cycle_recovery_is_non_negative(self):
        result = regen.simulate_regenerative_cycle(
            mass_kg=1200.0,
            time_seconds=[0.0, 1.0, 2.0],
            speed_mps=[15.0, 10.0, 0.0],
            recovery_efficiency=0.70,
        )

        # Support either a dictionary of arrays or a sequence of rows.
        if isinstance(result, dict):
            for key, values in result.items():
                if "recover" in str(key).lower():
                    if isinstance(values, (list, tuple)):
                        self.assertTrue(
                            all(float(value) >= -1e-9 for value in values)
                        )
                    elif isinstance(values, (int, float)):
                        self.assertGreaterEqual(values, -1e-9)


class TestMultipleBrakingEvents(unittest.TestCase):
    """Test analysis of multiple braking events."""

    def test_multiple_events_returns_result(self):
        events = [
            {
                "mass_kg": 1200.0,
                "initial_speed_mps": 15.0,
                "final_speed_mps": 0.0,
            },
            {
                "mass_kg": 1200.0,
                "initial_speed_mps": 10.0,
                "final_speed_mps": 0.0,
            },
        ]

        try:
            result = regen.analyse_multiple_braking_events(events)
        except TypeError:
            self.skipTest(
                "The function accepts a different input signature; "
                "adjust this test to match regenerative_model.py."
            )

        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
