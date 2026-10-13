
"""
Fluxxwave EV — Application Interface
=====================================

Provides a simple menu to:
1. Run the energy simulation.
2. Analyse logged simulation data.
3. Generate plots from recorded CSV data.
4. Open the output directory.
5. Exit.

Run:
    python app.py
"""

from pathlib import Path
import subprocess
import sys


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
LOG_DIR = ROOT / "data" / "logs"
ANALYSIS_DIR = ROOT / "data" / "analysis"

SAMPLES_FILE = LOG_DIR / "samples.csv"
EVENTS_FILE = LOG_DIR / "events.csv"


# ------------------------------------------------------------
# Display
# ------------------------------------------------------------

def print_header():
    print("\n" + "=" * 56)
    print("                 FLUXXWAVE EV")
    print("        Simulation and Performance Application")
    print("=" * 56)


def print_menu():
    print("\nChoose an operation:")
    print("1. Run energy simulation")
    print("2. Analyse simulation results")
    print("3. Generate plots from CSV logs")
    print("4. Open project output directory")
    print("5. Exit")


# ------------------------------------------------------------
# Simulation
# ------------------------------------------------------------

def run_simulation():
    """Execute the existing simulator."""
    print("\nStarting energy simulation...\n")

    try:
        from energy_simulator import run_simulation as simulate

        result = simulate()
        print("\nSimulation function finished.")

        if result is not None:
            print(f"Result type: {type(result).__name__}")

        if SAMPLES_FILE.exists() and SAMPLES_FILE.stat().st_size > 0:
            print(f"Sample log: {SAMPLES_FILE}")
        else:
            print(
                "Warning: samples.csv was not generated or is empty.\n"
                "Check that energy_simulator.py calls DataLogger."
            )

    except Exception as error:
        print(f"\nSimulation failed: {error}")
        print(
            "Check the imports and function signature in "
            "energy_simulator.py."
        )


# ------------------------------------------------------------
# Analysis
# ------------------------------------------------------------

def run_analysis():
    """Analyse previously recorded data."""
    if not SAMPLES_FILE.exists() or SAMPLES_FILE.stat().st_size == 0:
        print("\nNo recorded samples were found.")
        print(f"Expected file: {SAMPLES_FILE}")
        print("Run the simulation and connect the logger first.")
        return

    try:
        from analysis import run_analysis as analyse

        result = analyse(
            samples_file=SAMPLES_FILE,
            events_file=EVENTS_FILE,
            output_directory=ANALYSIS_DIR,
        )

        print("\nAnalysis finished.")

    except Exception as error:
        print(f"\nAnalysis failed: {error}")


# ------------------------------------------------------------
# Plotting
# ------------------------------------------------------------

def generate_plots():
    """Create charts using the plots.py module."""
    if not SAMPLES_FILE.exists() or SAMPLES_FILE.stat().st_size == 0:
        print("\nNo samples.csv found. Run the simulation first.")
        return

    try:
        from plots import generate_all_plots

        files = generate_all_plots(
            samples_file=SAMPLES_FILE,
            events_file=EVENTS_FILE,
            output_directory=ANALYSIS_DIR,
        )

        if files:
            print("\nGenerated plot files:")
            for filepath in files:
                print(f"- {filepath}")
        else:
            print("No plots could be generated from the available columns.")

    except ImportError as error:
        print(f"\nCould not import plotting dependencies: {error}")
        print("Install Matplotlib using:")
        print("python -m pip install matplotlib")

    except Exception as error:
        print(f"\nPlot generation failed: {error}")


# ------------------------------------------------------------
# Open output folder
# ------------------------------------------------------------

def open_output_directory():
    """Open the output folder using the operating system."""
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        if sys.platform.startswith("win"):
            import os
            os.startfile(str(ANALYSIS_DIR))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(ANALYSIS_DIR)])
        else:
            subprocess.Popen(["xdg-open", str(ANALYSIS_DIR)])

        print(f"Opening: {ANALYSIS_DIR}")

    except Exception as error:
        print(f"Could not open the directory: {error}")
        print(f"Open it manually: {ANALYSIS_DIR}")


# ------------------------------------------------------------
# Application loop
# ------------------------------------------------------------

def main():
    """Run the interactive application."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        print_header()
        print_menu()

        choice = input("\nEnter choice (1-5): ").strip()

        if choice == "1":
            run_simulation()

        elif choice == "2":
            run_analysis()

        elif choice == "3":
            generate_plots()

        elif choice == "4":
            open_output_directory()

        elif choice == "5":
            print("\nExiting Fluxxwave. Goodbye!")
            break

        else:
            print("\nInvalid choice. Enter a number from 1 to 5.")

        input("\nPress Enter to return to the menu...")


if __name__ == "__main__":
    main()
