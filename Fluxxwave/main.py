
"""
Fluxxwave EV — Main Application
================================

Central entry point for the Fluxxwave simulation project.

Execution order:
1. Run the energy simulation.
2. Check for generated logging files.
3. Analyse the recorded data.
4. Display a completion summary.

Run from the project root:
    python main.py

Important:
The simulator must be integrated with data_logger.py to generate
samples.csv and events.csv from the actual simulation. This file
does not create fake simulation data to conceal missing logs.
"""

from pathlib import Path
import sys
import traceback


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT_DIRECTORY = Path(__file__).resolve().parent

LOG_DIRECTORY = PROJECT_DIRECTORY / "data" / "logs"
ANALYSIS_DIRECTORY = PROJECT_DIRECTORY / "data" / "analysis"

SAMPLES_FILE = LOG_DIRECTORY / "samples.csv"
EVENTS_FILE = LOG_DIRECTORY / "events.csv"


# ============================================================
# 2. CONSOLE UTILITIES
# ============================================================

def print_header():
    """Display the Fluxxwave application header."""
    print("\n" + "=" * 60)
    print("                 FLUXXWAVE EV")
    print("        Solar-Assisted Electric Vehicle")
    print("           Simulation & Analysis")
    print("=" * 60)


def print_section(title):
    """Display a section heading."""
    print(f"\n{'-' * 60}")
    print(title)
    print("-" * 60)


def pause_if_needed():
    """Keep the terminal open when launched interactively."""
    # No input prompt: works in both terminals and automated runs.
    pass


# ============================================================
# 3. RUN THE SIMULATION
# ============================================================

def run_energy_simulation():
    """
    Import and execute the energy simulator.

    Returns:
        True if the simulation finishes without raising an error.
        False otherwise.
    """
    print_section("STEP 1 — ENERGY SIMULATION")

    try:
        from energy_simulator import run_simulation

        print("Starting Fluxxwave energy simulation...")

        result = run_simulation()

        print("Simulation function completed successfully.")

        if result is not None:
            print(f"Simulation result type: {type(result).__name__}")

        return True

    except ImportError as error:
        print("\nCould not import energy_simulator.py.")
        print(f"Details: {error}")
        print(
            "Check that energy_simulator.py is in the same "
            "folder as main.py and that its imports are available."
        )
        return False

    except Exception as error:
        print("\nThe energy simulation failed.")
        print(f"Error: {error}")
        print("\nTechnical details:")
        traceback.print_exc()
        return False


# ============================================================
# 4. CHECK LOG FILES
# ============================================================

def check_log_files():
    """
    Verify that the simulation produced the expected CSV files.

    Returns:
        True if samples.csv exists and contains data.
    """
    print_section("STEP 2 — CHECK SIMULATION LOGS")

    if not SAMPLES_FILE.exists():
        print("Simulation sample log was not found.")
        print(f"Expected location: {SAMPLES_FILE}")
        print("\nPossible reason:")
        print(
            "The simulation has not yet been connected to "
            "DataLogger.record_simulation_step()."
        )
        print("\nNext step:")
        print(
            "Integrate data_logger.py into energy_simulator.py, "
            "then run this application again."
        )
        return False

    if SAMPLES_FILE.stat().st_size == 0:
        print(f"The sample log is empty: {SAMPLES_FILE}")
        print("No recorded simulation samples are available.")
        return False

    print(f"Sample log found: {SAMPLES_FILE}")

    if EVENTS_FILE.exists():
        print(f"Event log found: {EVENTS_FILE}")
    else:
        print("No event log found.")
        print(
            "Switching analysis can continue with zero available "
            "event records, but switching statistics may be unavailable."
        )

    return True


# ============================================================
# 5. RUN PERFORMANCE ANALYSIS
# ============================================================

def run_performance_analysis():
    """
    Run analysis.py using absolute paths so execution does not depend
    on the terminal's current working directory.
    """
    print_section("STEP 3 — PERFORMANCE ANALYSIS")

    try:
        from analysis import run_analysis

        print("Analysing recorded simulation data...")

        result = run_analysis(
            samples_file=SAMPLES_FILE,
            events_file=EVENTS_FILE,
            output_directory=ANALYSIS_DIRECTORY,
        )

        print("\nAnalysis completed successfully.")
        return result

    except ImportError as error:
        print("Could not import analysis.py.")
        print(f"Details: {error}")
        return None

    except FileNotFoundError as error:
        print("Analysis input file is missing.")
        print(error)
        return None

    except Exception as error:
        print("Performance analysis failed.")
        print(f"Error: {error}")
        traceback.print_exc()
        return None


# ============================================================
# 6. DISPLAY FINAL STATUS
# ============================================================

def display_final_status(simulation_ok, logs_ok, analysis_result):
    """Display the outcome of the complete application run."""
    print_section("FLUXXWAVE RUN SUMMARY")

    print(
        f"Energy simulation: "
        f"{'SUCCESS' if simulation_ok else 'FAILED'}"
    )

    print(
        f"Simulation logs: "
        f"{'AVAILABLE' if logs_ok else 'MISSING OR EMPTY'}"
    )

    print(
        f"Performance analysis: "
        f"{'SUCCESS' if analysis_result is not None else 'NOT COMPLETED'}"
    )

    if analysis_result is not None:
        print(f"\nAnalysis output folder: {ANALYSIS_DIRECTORY}")

    elif simulation_ok and not logs_ok:
        print(
            "\nThe simulation ran, but its recorded data could not "
            "be analysed because the expected log file is missing."
        )

    print("\nFluxxwave application finished.")
    print("=" * 60)


# ============================================================
# 7. MAIN APPLICATION
# ============================================================

def main():
    """Run the Fluxxwave application from beginning to end."""
    print_header()

    # Create output directories if they do not already exist.
    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    ANALYSIS_DIRECTORY.mkdir(parents=True, exist_ok=True)

    simulation_ok = run_energy_simulation()

    # Check logs even if the simulation function completed.
    # A successful simulation does not guarantee that logging works.
    logs_ok = check_log_files() if simulation_ok else False

    analysis_result = None

    if simulation_ok and logs_ok:
        analysis_result = run_performance_analysis()
    else:
        print_section("ANALYSIS SKIPPED")
        print(
            "Analysis requires a non-empty samples.csv file "
            "containing recorded simulation results."
        )

    display_final_status(
        simulation_ok,
        logs_ok,
        analysis_result,
    )

    # Return a non-zero exit status when the full pipeline did not finish.
    return 0 if (
        simulation_ok
        and logs_ok
        and analysis_result is not None
    ) else 1


if __name__ == "__main__":
    sys.exit(main())
