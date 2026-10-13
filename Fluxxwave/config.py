
"""
Fluxxwave EV — Central Configuration
=====================================

Purpose:
- Store simulation constants and default parameters.
- Configure solar generation, vehicle dynamics, regenerative braking,
  battery behaviour, battery switching, and data logging.
- Provide a single source of default values for the project.

IMPORTANT:
These settings are for software simulation only. They are not validated
hardware specifications and must not be used directly to control a
physical traction battery or vehicle.
"""

from pathlib import Path


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_DIRECTORY = PROJECT_ROOT / "data"
LOG_DIRECTORY = DATA_DIRECTORY / "logs"
ANALYSIS_DIRECTORY = DATA_DIRECTORY / "analysis"
DASHBOARD_DIRECTORY = DATA_DIRECTORY / "dashboard"

# Common input and output files
SAMPLES_FILE = LOG_DIRECTORY / "samples.csv"
EVENTS_FILE = LOG_DIRECTORY / "events.csv"
METADATA_FILE = LOG_DIRECTORY / "metadata.json"

ANALYSIS_SUMMARY_FILE = ANALYSIS_DIRECTORY / "summary.csv"
ANALYSIS_REPORT_FILE = ANALYSIS_DIRECTORY / "report.md"
ANALYSIS_GRAPH_FILE = ANALYSIS_DIRECTORY / "energy_analysis.png"


# ============================================================
# 2. SIMULATION SETTINGS
# ============================================================

SIMULATION_CONFIG = {
    # Total simulated duration: 1 hour
    "duration_seconds": 3600,

    # Simulation updates once per minute
    "step_seconds": 60,

    # Initial vehicle speed
    "initial_speed_mps": 0.0,

    # Reproducibility for synthetic demo profiles
    "random_seed": 42,
}


# ============================================================
# 3. SOLAR PANEL SETTINGS
# ============================================================

SOLAR_CONFIG = {
    # Total effective solar-panel area
    "panel_area_m2": 2.0,

    # Panel conversion efficiency: 22%
    "panel_efficiency": 0.22,

    # Solar irradiance is provided by the simulation profile
    "peak_irradiance_w_m2": 900.0,

    # Fraction of panel output lost through system inefficiencies
    "system_efficiency": 0.95,

    # 0.0 = no shading; 1.0 = fully shaded
    "shading_fraction": 0.0,

    # Simplified temperature model
    "reference_temperature_c": 25.0,
    "temperature_coefficient_per_c": -0.004,
}


# ============================================================
# 4. VEHICLE PARAMETERS
# ============================================================

VEHICLE_CONFIG = {
    # Illustrative simulation values
    "mass_kg": 1200.0,

    # Aerodynamic drag coefficient
    "drag_coefficient": 0.29,

    # Frontal area in square metres
    "frontal_area_m2": 2.2,

    # Approximate air density
    "air_density_kg_m3": 1.225,

    # Dimensionless rolling-resistance coefficient
    "rolling_resistance_coefficient": 0.012,

    # Simplified drivetrain efficiency
    "drivetrain_efficiency": 0.90,

    # Auxiliary electrical load
    "auxiliary_power_w": 300.0,

    # Gravitational acceleration
    "gravity_m_s2": 9.80665,
}


# ============================================================
# 5. REGENERATIVE BRAKING SETTINGS
# ============================================================

REGENERATIVE_CONFIG = {
    # Assumed fraction of available braking energy recovered
    "recovery_efficiency": 0.70,

    # Fraction of the kinetic-energy decrease treated as available
    # for regenerative recovery in the simplified model
    "braking_energy_availability_factor": 0.80,

    # Optional correction for rotating components
    "rotational_energy_factor": 0.0,
}


# ============================================================
# 6. BATTERY SETTINGS
# ============================================================

BATTERY_CONFIG = {
    # Example battery capacities
    "capacity_kwh": 2.0,
    "nominal_voltage_v": 48.0,

    # Initial battery state of charge
    "battery_a_initial_soc_percent": 80.0,
    "battery_b_initial_soc_percent": 90.0,

    # Permitted range for the simplified battery simulation
    "minimum_soc_percent": 20.0,
    "maximum_soc_percent": 100.0,

    # Simplified operating-temperature limits
    "minimum_temperature_c": 0.0,
    "maximum_temperature_c": 45.0,

    # Simplified power limits
    "maximum_discharge_power_w": 1500.0,
    "maximum_charge_power_w": 1000.0,

    # Assumed charging efficiency
    "charge_efficiency": 0.95,

    # Assumed discharging efficiency used by the energy simulator
    "discharge_efficiency": 0.95,
}


# ============================================================
# 7. BATTERY-MANAGEMENT SETTINGS
# ============================================================

BATTERY_MANAGER_CONFIG = {
    # Switch away from an active battery at or below this SoC
    "switch_threshold_percent": 20.0,

    # Hysteresis prevents repeated switching near the threshold
    "hysteresis_percent": 5.0,

    # Minimum interval between switching attempts
    "minimum_switch_interval_seconds": 10.0,
}


# ============================================================
# 8. ENERGY-MANAGEMENT SETTINGS
# ============================================================

ENERGY_MANAGEMENT_CONFIG = {
    # Maximum acceptable numerical energy-balance discrepancy
    "energy_balance_tolerance_kwh": 1e-6,

    # Record solar and regenerative energy flows separately
    "track_solar_energy": True,
    "track_regenerative_energy": True,

    # Record charging and discharging losses
    "track_conversion_losses": True,
}


# ============================================================
# 9. DATA LOGGER SETTINGS
# ============================================================

LOGGER_CONFIG = {
    "output_directory": LOG_DIRECTORY,
    "samples_filename": "samples.csv",
    "events_filename": "events.csv",
    "metadata_filename": "metadata.json",

    # Mark logs as simulation data, not measured hardware data
    "data_source": "simulation",

    # Record simulation estimates at every step
    "record_every_step": True,

    # Save records after the simulation finishes
    "save_after_simulation": True,
}


# ============================================================
# 10. ANALYSIS SETTINGS
# ============================================================

ANALYSIS_CONFIG = {
    "output_directory": ANALYSIS_DIRECTORY,
    "default_step_seconds": SIMULATION_CONFIG["step_seconds"],

    "generate_graphs": True,
    "generate_markdown_report": True,
    "compare_scenarios": True,
}


# ============================================================
# 11. DASHBOARD SETTINGS
# ============================================================

DASHBOARD_CONFIG = {
    "output_directory": DASHBOARD_DIRECTORY,
    "save_figures": True,
    "show_figures": True,
}


# ============================================================
# 12. VALIDATION
# ============================================================

def validate_config():
    """
    Check basic configuration consistency.

    This is a software-configuration check, not a hardware safety test.
    Raises ValueError when a parameter is clearly invalid.
    """

    if SIMULATION_CONFIG["duration_seconds"] <= 0:
        raise ValueError("Simulation duration must be positive.")

    if SIMULATION_CONFIG["step_seconds"] <= 0:
        raise ValueError("Simulation step must be positive.")

    if (
        SIMULATION_CONFIG["duration_seconds"]
        < SIMULATION_CONFIG["step_seconds"]
    ):
        raise ValueError(
            "Simulation duration must be at least one time step."
        )

    if VEHICLE_CONFIG["mass_kg"] <= 0:
        raise ValueError("Vehicle mass must be positive.")

    if SOLAR_CONFIG["panel_area_m2"] < 0:
        raise ValueError("Panel area cannot be negative.")

    if not 0.0 <= SOLAR_CONFIG["panel_efficiency"] <= 1.0:
        raise ValueError("Panel efficiency must be between 0 and 1.")

    if not 0.0 <= SOLAR_CONFIG["system_efficiency"] <= 1.0:
        raise ValueError("Solar system efficiency must be between 0 and 1.")

    if not 0.0 <= SOLAR_CONFIG["shading_fraction"] <= 1.0:
        raise ValueError("Shading fraction must be between 0 and 1.")

    if not 0.0 <= REGENERATIVE_CONFIG["recovery_efficiency"] <= 1.0:
        raise ValueError(
            "Regenerative recovery efficiency must be between 0 and 1."
        )

    if not (
        0.0
        <= REGENERATIVE_CONFIG["braking_energy_availability_factor"]
        <= 1.0
    ):
        raise ValueError(
            "Braking-energy availability factor must be between 0 and 1."
        )

    if BATTERY_CONFIG["capacity_kwh"] <= 0:
        raise ValueError("Battery capacity must be positive.")

    if BATTERY_CONFIG["nominal_voltage_v"] <= 0:
        raise ValueError("Nominal battery voltage must be positive.")

    for key in (
        "battery_a_initial_soc_percent",
        "battery_b_initial_soc_percent",
    ):
        soc = BATTERY_CONFIG[key]
        if not 0.0 <= soc <= 100.0:
            raise ValueError(f"{key} must be between 0 and 100.")

    minimum_soc = BATTERY_CONFIG["minimum_soc_percent"]
    maximum_soc = BATTERY_CONFIG["maximum_soc_percent"]

    if not 0.0 <= minimum_soc < maximum_soc <= 100.0:
        raise ValueError("Battery SoC limits are inconsistent.")

    if not 0.0 < BATTERY_CONFIG["charge_efficiency"] <= 1.0:
        raise ValueError("Charge efficiency must be greater than 0 and at most 1.")

    if not 0.0 < BATTERY_CONFIG["discharge_efficiency"] <= 1.0:
        raise ValueError(
            "Discharge efficiency must be greater than 0 and at most 1."
        )

    if not 0.0 <= BATTERY_MANAGER_CONFIG["switch_threshold_percent"] <= 100.0:
        raise ValueError("Switch threshold must be between 0 and 100.")

    if BATTERY_MANAGER_CONFIG["minimum_switch_interval_seconds"] < 0:
        raise ValueError("Switch interval cannot be negative.")

    return True


# ============================================================
# 13. DIRECTORY INITIALIZATION
# ============================================================

def create_project_directories():
    """Create data directories if they do not already exist."""
    for directory in (
        DATA_DIRECTORY,
        LOG_DIRECTORY,
        ANALYSIS_DIRECTORY,
        DASHBOARD_DIRECTORY,
    ):
        directory.mkdir(parents=True, exist_ok=True)


# ============================================================
# 14. CONFIGURATION SUMMARY
# ============================================================

def print_config_summary():
    """Print a compact summary of the active simulation settings."""
    print("\n" + "=" * 55)
    print("FLUXXWAVE CONFIGURATION")
    print("=" * 55)

    print("\nSimulation:")
    for key, value in SIMULATION_CONFIG.items():
        print(f"  {key}: {value}")

    print("\nSolar:")
    for key, value in SOLAR_CONFIG.items():
        print(f"  {key}: {value}")

    print("\nVehicle:")
    for key, value in VEHICLE_CONFIG.items():
        print(f"  {key}: {value}")

    print("\nRegenerative braking:")
    for key, value in REGENERATIVE_CONFIG.items():
        print(f"  {key}: {value}")

    print("\nBattery management:")
    for key, value in BATTERY_MANAGER_CONFIG.items():
        print(f"  {key}: {value}")

    print("\nData paths:")
    print(f"  Project root: {PROJECT_ROOT}")
    print(f"  Logs: {LOG_DIRECTORY}")
    print(f"  Analysis: {ANALYSIS_DIRECTORY}")
    print("=" * 55)


# ============================================================
# 15. DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":
    validate_config()
    create_project_directories()
    print_config_summary()
    print("\nConfiguration validation passed.")
