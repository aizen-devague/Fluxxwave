
"""
Fluxxwave EV — Plotting and Visualisation
==========================================

Generates graphs from recorded CSV simulation data.

Supported visualisations:
1. Solar and regenerative power.
2. Vehicle demand and battery power.
3. Battery state of charge.
4. Recorded energy totals.
5. Battery switching events.

Input:
    data/logs/samples.csv
    data/logs/events.csv

Output:
    data/analysis/plots/

Dependency:
    matplotlib

Run:
    python plots.py
"""

from pathlib import Path
import csv
import re


# ============================================================
# 1. PATHS AND COLUMN ALIASES
# ============================================================

ROOT = Path(__file__).resolve().parent

DEFAULT_SAMPLES_FILE = ROOT / "data" / "logs" / "samples.csv"
DEFAULT_EVENTS_FILE = ROOT / "data" / "logs" / "events.csv"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "analysis" / "plots"

ALIASES = {
    "solar_power": [
        "solar_power_w",
        "solar_generated_power_w",
        "solar_generation_power_w",
        "solar_power",
    ],
    "regen_power": [
        "regenerative_power_w",
        "regen_power_w",
        "recovered_power_w",
        "regenerative_power",
    ],
    "load_power": [
        "load_power_w",
        "vehicle_demand_power_w",
        "vehicle_load_power_w",
        "demand_power_w",
        "load_power",
    ],
    "battery_power": [
        "battery_power_w",
        "battery_to_load_power_w",
        "battery_discharge_power_w",
    ],
    "soc_a": [
        "battery_a_soc_percent",
        "battery_a_soc",
        "battery_a_soc_pct",
        "soc_a_percent",
    ],
    "soc_b": [
        "battery_b_soc_percent",
        "battery_b_soc",
        "battery_b_soc_pct",
        "soc_b_percent",
    ],
    "solar_energy": [
        "solar_energy_kwh",
        "solar_generated_energy_kwh",
        "solar_generation_kwh",
        "solar_energy_wh",
        "solar_energy",
    ],
    "regen_energy": [
        "regenerative_energy_kwh",
        "recovered_energy_kwh",
        "regen_energy_kwh",
        "regenerative_energy_wh",
        "regen_energy",
    ],
    "load_energy": [
        "load_energy_kwh",
        "vehicle_demand_kwh",
        "vehicle_load_kwh",
        "total_load_kwh",
        "load_energy_wh",
    ],
    "battery_stored": [
        "battery_energy_stored_kwh",
        "battery_energy_added_kwh",
        "battery_stored_kwh",
    ],
    "battery_removed": [
        "battery_energy_removed_kwh",
        "battery_energy_consumed_kwh",
        "battery_to_load_kwh",
        "battery_discharge_kwh",
    ],
    "losses": [
        "total_modeled_losses_kwh",
        "conversion_loss_kwh",
        "charge_loss_kwh",
        "discharge_loss_kwh",
    ],
    "timestamp": [
        "timestamp_utc",
        "timestamp",
        "time",
        "datetime",
    ],
}


# ============================================================
# 2. CSV UTILITIES
# ============================================================

def normalize_name(name):
    """Normalize a field name for case-insensitive matching."""
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def read_csv(filepath):
    """Read CSV rows as dictionaries."""
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        return list(csv.DictReader(file))


def find_column(rows, aliases):
    """Find the first matching column name."""
    if not rows:
        return None

    available = {
        normalize_name(key): key
        for row in rows
        for key in row.keys()
    }

    for alias in aliases:
        match = available.get(normalize_name(alias))
        if match is not None:
            return match

    return None


def numeric_value(value):
    """Convert a value to a finite float or return None."""
    import math

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    return number


def get_series(rows, metric):
    """
    Return the row indices and numeric values for a metric.

    Missing values are skipped. Returned indices preserve the
    positions of the original rows.
    """
    column = find_column(rows, ALIASES.get(metric, [metric]))

    if column is None:
        return None, [], []

    indices = []
    values = []

    for index, row in enumerate(rows):
        number = numeric_value(row.get(column))

        if number is not None:
            indices.append(index)
            values.append(number)

    return column, indices, values


def energy_to_kwh(value, column_name):
    """Convert Wh or joules to kWh; otherwise assume kWh."""
    name = normalize_name(column_name)

    if "wh" in name and "kwh" not in name:
        return value / 1000.0

    if "joule" in name or name.endswith("j"):
        return value / 3_600_000.0

    return value


def power_to_kw(value, column_name):
    """Convert watts to kW when needed."""
    name = normalize_name(column_name)

    if "kw" in name:
        return value

    return value / 1000.0


def safe_filename(name):
    """Create a filesystem-friendly filename."""
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", name).strip("_").lower()


# ============================================================
# 3. MATPLOTLIB SETUP
# ============================================================

def get_matplotlib():
    """Import Matplotlib only when graphing is requested."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except ImportError as error:
        raise ImportError(
            "Matplotlib is required for plots. Install it with:\n"
            "python -m pip install matplotlib"
        ) from error


def finish_plot(fig, output_path, show=False):
    """Save a figure and optionally display it."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig.tight_layout()
    fig.savefig(output_path, dpi=160)

    if show:
        import matplotlib.pyplot as plt
        plt.show()

    import matplotlib.pyplot as plt
    plt.close(fig)

    print(f"Saved plot: {output_path}")
    return output_path


def x_axis(rows, indices):
    """Use recorded timestamps if available; otherwise use step number."""
    column = find_column(rows, ALIASES["timestamp"])

    if column:
        labels = [rows[index].get(column, "") for index in indices]
        if any(label for label in labels):
            return labels, "Timestamp"

    return [index + 1 for index in indices], "Simulation step"


# ============================================================
# 4. POWER PLOT
# ============================================================

def plot_power_flows(
    rows,
    output_dir=DEFAULT_OUTPUT_DIR,
    show=False,
):
    """Plot available solar, regenerative, load and battery power."""
    plt = get_matplotlib()

    metrics = [
        ("solar_power", "Solar power"),
        ("regen_power", "Regenerative power"),
        ("load_power", "Vehicle demand power"),
        ("battery_power", "Battery power"),
    ]

    series = []

    for metric, label in metrics:
        column, indices, values = get_series(rows, metric)

        if column and values:
            values_kw = [power_to_kw(v, column) for v in values]
            series.append((label, indices, values_kw))

    if not series:
        print("Skipping power graph: no supported power columns found.")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    for label, indices, values in series:
        labels, x_label = x_axis(rows, indices)
        ax.plot(labels, values, label=label)

    ax.set_title("Fluxxwave — Power Flows")
    ax.set_xlabel(x_label)
    ax.set_ylabel("Power (kW)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    return finish_plot(
        fig,
        Path(output_dir) / "power_flows.png",
        show,
    )


# ============================================================
# 5. BATTERY STATE OF CHARGE
# ============================================================

def plot_battery_soc(
    rows,
    output_dir=DEFAULT_OUTPUT_DIR,
    show=False,
):
    """Plot recorded battery state-of-charge values."""
    plt = get_matplotlib()

    metrics = [
        ("soc_a", "Battery A SoC"),
        ("soc_b", "Battery B SoC"),
    ]

    series = []

    for metric, label in metrics:
        column, indices, values = get_series(rows, metric)

        if column and values:
            series.append((label, indices, values))

    if not series:
        print("Skipping SoC graph: no supported SoC columns found.")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))

    for label, indices, values in series:
        labels, x_label = x_axis(rows, indices)
        ax.plot(labels, values, label=label)

    ax.set_title("Fluxxwave — Battery State of Charge")
    ax.set_xlabel(x_label)
    ax.set_ylabel("State of charge (%)")
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)
    ax.legend()

    return finish_plot(
        fig,
        Path(output_dir) / "battery_soc.png",
        show,
    )


# ============================================================
# 6. ENERGY TOTALS
# ============================================================

def plot_energy_totals(
    rows,
    output_dir=DEFAULT_OUTPUT_DIR,
    show=False,
):
    """
    Plot the sum of recorded energy fields.

    This graph compares reported quantities; it is not an energy
    balance equation. Some values may describe different stages of
    the same energy flow and must not be added together.
    """
    plt = get_matplotlib()

    metrics = [
        ("solar_energy", "Solar energy"),
        ("regen_energy", "Regenerative energy"),
        ("load_energy", "Vehicle load energy"),
        ("battery_stored", "Battery energy stored"),
        ("battery_removed", "Battery energy removed"),
        ("losses", "Recorded losses"),
    ]

    labels = []
    values = []

    for metric, label in metrics:
        column, _, raw_values = get_series(rows, metric)

        if column and raw_values:
            total = sum(
                energy_to_kwh(value, column)
                for value in raw_values
            )

            labels.append(label)
            values.append(total)

    if not values:
        print("Skipping energy graph: no supported energy columns found.")
        return None

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(labels, values)

    ax.set_title("Fluxxwave — Recorded Energy Metrics")
    ax.set_ylabel("Energy (kWh)")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.3)

    return finish_plot(
        fig,
        Path(output_dir) / "energy_totals.png",
        show,
    )


# ============================================================
# 7. BATTERY SWITCHING EVENTS
# ============================================================

def plot_switching_events(
    events,
    output_dir=DEFAULT_OUTPUT_DIR,
    show=False,
):
    """Plot cumulative battery-switching events when available."""
    plt = get_matplotlib()

    if not events:
        print("Skipping switching graph: no event records found.")
        return None

    type_column = find_column(
        events,
        ["event_type", "type", "event"],
    )

    from_column = find_column(
        events,
        ["from_battery", "source_battery", "previous_battery"],
    )

    to_column = find_column(
        events,
        ["to_battery", "target_battery", "new_battery"],
    )

    switch_indices = []

    for index, event in enumerate(events):
        event_type = (
            str(event.get(type_column, "")).lower()
            if type_column else ""
        )

        has_transition = (
            from_column is not None
            and to_column is not None
            and event.get(from_column)
            and event.get(to_column)
        )

        if "switch" in event_type or has_transition:
            switch_indices.append(index + 1)

    if not switch_indices:
        print("No identifiable battery-switching events were found.")
        return None

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.step(
        switch_indices,
        range(1, len(switch_indices) + 1),
        where="post",
    )

    ax.set_title("Fluxxwave — Cumulative Battery Switches")
    ax.set_xlabel("Event record index")
    ax.set_ylabel("Cumulative switching events")
    ax.grid(True, alpha=0.3)

    return finish_plot(
        fig,
        Path(output_dir) / "battery_switching.png",
        show,
    )


# ============================================================
# 8. GENERATE ALL AVAILABLE PLOTS
# ============================================================

def generate_all_plots(
    samples_file=DEFAULT_SAMPLES_FILE,
    events_file=DEFAULT_EVENTS_FILE,
    output_directory=DEFAULT_OUTPUT_DIR,
    show=False,
):
    """Generate all charts supported by the supplied CSV files."""
    samples = read_csv(samples_file)

    if not samples:
        print("The samples CSV contains no data rows.")
        return []

    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)

    events_path = Path(events_file)
    events = read_csv(events_path) if events_path.exists() else []

    generated = []

    plot_functions = [
        lambda: plot_power_flows(samples, output_dir, show),
        lambda: plot_battery_soc(samples, output_dir, show),
        lambda: plot_energy_totals(samples, output_dir, show),
        lambda: plot_switching_events(events, output_dir, show),
    ]

    for plot_function in plot_functions:
        result = plot_function()

        if result is not None:
            generated.append(result)

    print(f"\nGenerated {len(generated)} plot(s).")
    return generated


# ============================================================
# 9. DIRECT EXECUTION
# ============================================================

def main():
    """Run the plotting module independently."""
    try:
        generate_all_plots()
    except FileNotFoundError as error:
        print(f"\nCannot generate plots:\n{error}")
    except ImportError as error:
        print(f"\nDependency error:\n{error}")


if __name__ == "__main__":
    main()
