
"""
Fluxxwave EV — Performance Analysis Module
===========================================

Responsibilities:
1. Calculate total simulated energy consumption.
2. Summarize solar generation and regenerative braking recovery.
3. Quantify modeled conversion losses.
4. Summarize battery switching events.
5. Compare multiple simulation scenarios.
6. Export CSV summaries, graphs, and a Markdown report.

Default inputs:
    data/logs/samples.csv
    data/logs/events.csv

Default outputs:
    data/analysis/summary.csv
    data/analysis/scenario_comparison.csv
    data/analysis/switching_summary.csv
    data/analysis/energy_analysis.png   (if matplotlib is installed)
    data/analysis/report.md

IMPORTANT:
- This module analyses SIMULATED data, not measured hardware data.
- Energy values are expected in kWh unless their column names
  explicitly indicate Wh, J, or another supported unit.
- Power values are expected in W unless their column names indicate kW.
- Missing measurements are reported as unavailable, not assumed to be zero.
- Do not add power values directly to energy values.
"""

from __future__ import annotations

import csv
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


# ============================================================
# 1. CONFIGURATION
# ============================================================

DEFAULT_LOG_DIRECTORY = Path("data/logs")
DEFAULT_OUTPUT_DIRECTORY = Path("data/analysis")

DEFAULT_SAMPLES_FILE = DEFAULT_LOG_DIRECTORY / "samples.csv"
DEFAULT_EVENTS_FILE = DEFAULT_LOG_DIRECTORY / "events.csv"

ENERGY_SUMMARY_FILE = DEFAULT_OUTPUT_DIRECTORY / "summary.csv"
SCENARIO_COMPARISON_FILE = (
    DEFAULT_OUTPUT_DIRECTORY / "scenario_comparison.csv"
)
SWITCHING_SUMMARY_FILE = (
    DEFAULT_OUTPUT_DIRECTORY / "switching_summary.csv"
)
GRAPH_FILE = DEFAULT_OUTPUT_DIRECTORY / "energy_analysis.png"
REPORT_FILE = DEFAULT_OUTPUT_DIRECTORY / "report.md"

# Default time step is only used when timestamps and explicit
# time-step information are unavailable.
DEFAULT_STEP_SECONDS = 60.0

# Numerical tolerance for small floating-point differences.
EPSILON = 1e-12


# ============================================================
# 2. COLUMN ALIASES
# ============================================================

# The logger's exact column names depend on the implementation.
# These aliases support common naming conventions.
#
# Extend these lists if your CSV uses different field names.

ALIASES = {
    "solar_energy": [
        "solar_energy_kwh",
        "solar_generated_energy_kwh",
        "solar_generation_kwh",
        "solar_input_kwh",
        "solar_energy_wh",
        "solar_energy_j",
        "solar_energy_joules",
        "solar_energy",
    ],
    "solar_power": [
        "solar_power_w",
        "solar_generated_power_w",
        "solar_generation_power_w",
        "solar_power",
    ],
    "regen_energy": [
        "regenerative_energy_kwh",
        "recovered_energy_kwh",
        "regen_energy_kwh",
        "regenerative_recovered_kwh",
        "regenerative_energy_wh",
        "regen_energy_wh",
        "regenerative_energy_j",
        "recovered_energy_j",
        "regen_energy",
    ],
    "regen_power": [
        "regenerative_power_w",
        "regen_power_w",
        "recovered_power_w",
        "regenerative_power",
    ],
    "load_energy": [
        "load_energy_kwh",
        "vehicle_demand_kwh",
        "vehicle_load_kwh",
        "total_load_kwh",
        "energy_demand_kwh",
        "load_energy_wh",
        "load_energy",
    ],
    "load_power": [
        "load_power_w",
        "vehicle_demand_power_w",
        "vehicle_load_power_w",
        "demand_power_w",
        "load_power",
    ],
    "battery_removed": [
        "battery_energy_removed_kwh",
        "battery_energy_consumed_kwh",
        "battery_to_load_kwh",
        "battery_discharge_kwh",
        "battery_removed_kwh",
    ],
    "battery_stored": [
        "battery_energy_stored_kwh",
        "battery_energy_added_kwh",
        "battery_charge_stored_kwh",
        "battery_stored_kwh",
    ],
    "charge_loss": [
        "charge_loss_kwh",
        "charging_loss_kwh",
        "battery_charge_loss_kwh",
    ],
    "discharge_loss": [
        "discharge_loss_kwh",
        "battery_discharge_loss_kwh",
    ],
    "conversion_loss": [
        "conversion_loss_kwh",
        "total_conversion_loss_kwh",
        "system_conversion_loss_kwh",
    ],
    "curtailed_energy": [
        "curtailed_energy_kwh",
        "unused_energy_kwh",
        "curtailed_kwh",
    ],
    "unmet_demand": [
        "unmet_vehicle_demand_kwh",
        "unmet_demand_kwh",
        "unserved_energy_kwh",
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
    "timestamp": [
        "timestamp_utc",
        "timestamp",
        "time",
        "datetime",
    ],
    "step_seconds": [
        "step_seconds",
        "duration_seconds",
        "interval_seconds",
        "dt_seconds",
    ],
}


# ============================================================
# 3. GENERAL UTILITIES
# ============================================================

def normalize_name(value: str) -> str:
    """Normalize a column name for case-insensitive matching."""
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def to_number(value: Any) -> float | None:
    """Convert a CSV value to a finite float, if possible."""
    if value is None or isinstance(value, bool):
        return None

    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None

    if not math.isfinite(result):
        return None

    return result


def load_csv(filepath: str | Path) -> list[dict[str, str]]:
    """Load a CSV file as a list of dictionaries."""
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(
            f"Input file not found: {path}\n"
            "Run the Fluxxwave simulation and logger first."
        )

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))


def write_csv(
    filepath: str | Path,
    records: list[dict[str, Any]],
) -> None:
    """Write dictionaries to CSV, creating the parent directory."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not records:
        # No columns are known when there are no records.
        path.write_text("", encoding="utf-8")
        return

    columns = list(dict.fromkeys(
        key
        for record in records
        for key in record.keys()
    ))

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=columns,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(records)


def find_column(
    records: list[dict[str, Any]],
    aliases: Iterable[str],
) -> str | None:
    """Find a matching field without assuming a specific capitalization."""
    if not records:
        return None

    existing = {
        normalize_name(key): key
        for record in records
        for key in record.keys()
    }

    for alias in aliases:
        match = existing.get(normalize_name(alias))
        if match is not None:
            return match

    return None


def extract_values(
    records: list[dict[str, Any]],
    metric: str,
) -> tuple[list[float], str | None]:
    """Extract numeric values for a named metric."""
    aliases = ALIASES.get(metric, [metric])
    column = find_column(records, aliases)

    if column is None:
        return [], None

    values = [
        number
        for row in records
        if (number := to_number(row.get(column))) is not None
    ]

    return values, column


def convert_energy_to_kwh(
    value: float,
    column_name: str,
) -> float:
    """Convert supported energy columns to kWh."""
    name = normalize_name(column_name)

    if "wh" in name and "kwh" not in name:
        return value / 1000.0

    # Joules: handle common spellings.
    if "joule" in name or name.endswith("j"):
        return value / 3_600_000.0

    # Bare energy column names are assumed to use kWh.
    return value


def convert_power_to_kw(
    value: float,
    column_name: str,
) -> float:
    """Convert supported power columns to kW."""
    name = normalize_name(column_name)

    if "kw" in name:
        return value

    return value / 1000.0


def sum_energy(
    records: list[dict[str, Any]],
    metric: str,
) -> float | None:
    """
    Sum an explicitly recorded energy metric.

    Returns None when no matching field exists.
    Negative energy values are retained because they may indicate
    a signed energy-flow convention.
    """
    values, column = extract_values(records, metric)

    if column is None:
        return None

    return sum(
        convert_energy_to_kwh(value, column)
        for value in values
    )


def mean_value(
    records: list[dict[str, Any]],
    metric: str,
) -> float | None:
    """Return the arithmetic mean of a recorded numeric metric."""
    values, _ = extract_values(records, metric)

    if not values:
        return None

    return sum(values) / len(values)


def fmt(value: Any, digits: int = 4) -> str:
    """Format a number or unavailable result for reports."""
    if value is None:
        return "Unavailable"

    if isinstance(value, float) and not math.isfinite(value):
        return "Unavailable"

    return f"{value:.{digits}f}" if isinstance(value, float) else str(value)


# ============================================================
# 4. ENERGY CALCULATIONS
# ============================================================

def integrate_power(
    records: list[dict[str, Any]],
    metric: str,
    default_step_seconds: float = DEFAULT_STEP_SECONDS,
) -> float | None:
    """
    Estimate energy by integrating power over time.

    Uses trapezoidal integration when a sequence of power samples
    and a usable time interval are available.

    If timestamps are missing, assumes a fixed step duration.
    This fallback is an assumption, not measured timing data.

    The last power sample is not extended by another time interval.
    """
    values, column = extract_values(records, metric)

    if column is None or len(values) < 2:
        return None

    powers_kw = [
        convert_power_to_kw(value, column)
        for value in values
    ]

    timestamp_column = find_column(
        records,
        ALIASES["timestamp"],
    )
    step_column = find_column(
        records,
        ALIASES["step_seconds"],
    )

    # Pair valid power samples with their original rows.
    pairs = []
    for row in records:
        number = to_number(row.get(column))
        if number is None:
            continue

        power_kw = convert_power_to_kw(number, column)
        timestamp = None

        if timestamp_column:
            raw_timestamp = row.get(timestamp_column)
            if raw_timestamp:
                try:
                    timestamp = datetime.fromisoformat(
                        str(raw_timestamp).replace("Z", "+00:00")
                    )
                except ValueError:
                    timestamp = None

        step = (
            to_number(row.get(step_column))
            if step_column
            else None
        )

        pairs.append((power_kw, timestamp, step))

    if len(pairs) < 2:
        return None

    total_kwh = 0.0

    for index in range(1, len(pairs)):
        previous_power, previous_time, previous_step = pairs[index - 1]
        current_power, current_time, current_step = pairs[index]

        seconds = None

        if previous_time is not None and current_time is not None:
            seconds = (current_time - previous_time).total_seconds()

        if seconds is None or seconds <= 0:
            seconds = current_step or previous_step or default_step_seconds

        if seconds <= 0:
            continue

        total_kwh += (
            (previous_power + current_power) / 2.0
        ) * seconds / 3600.0

    return total_kwh


def energy_metric(
    records: list[dict[str, Any]],
    energy_key: str,
    power_key: str,
    default_step_seconds: float = DEFAULT_STEP_SECONDS,
) -> float | None:
    """
    Prefer recorded energy. Fall back to power integration if needed.
    """
    direct = sum_energy(records, energy_key)

    if direct is not None:
        return direct

    return integrate_power(
        records,
        power_key,
        default_step_seconds,
    )


def calculate_total_energy(
    samples: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Calculate the principal energy totals.

    The function reports unavailable values explicitly. It does not
    infer total consumption from solar generation or regen recovery.
    """
    solar = energy_metric(samples, "solar_energy", "solar_power")
    regen = energy_metric(samples, "regen_energy", "regen_power")
    load = energy_metric(samples, "load_energy", "load_power")

    battery_removed = sum_energy(samples, "battery_removed")
    battery_stored = sum_energy(samples, "battery_stored")
    charge_loss = sum_energy(samples, "charge_loss")
    discharge_loss = sum_energy(samples, "discharge_loss")
    conversion_loss = sum_energy(samples, "conversion_loss")
    curtailed = sum_energy(samples, "curtailed_energy")
    unmet = sum_energy(samples, "unmet_demand")

    if charge_loss is None and discharge_loss is None:
        modeled_battery_losses = None
    else:
        modeled_battery_losses = (
            (charge_loss or 0.0) + (discharge_loss or 0.0)
        )

    if conversion_loss is not None:
        total_modeled_losses = conversion_loss
    else:
        total_modeled_losses = modeled_battery_losses

    return {
        "recorded_steps": len(samples),
        "solar_energy_kwh": solar,
        "regenerative_energy_kwh": regen,
        "vehicle_load_energy_kwh": load,
        "battery_energy_removed_kwh": battery_removed,
        "battery_energy_stored_kwh": battery_stored,
        "battery_charge_loss_kwh": charge_loss,
        "battery_discharge_loss_kwh": discharge_loss,
        "battery_losses_kwh": modeled_battery_losses,
        "conversion_loss_kwh": conversion_loss,
        "total_modeled_losses_kwh": total_modeled_losses,
        "curtailed_energy_kwh": curtailed,
        "unmet_demand_kwh": unmet,
    }


def calculate_efficiency(
    totals: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate explicitly defined contribution and recovery ratios.

    Solar contribution ratio:
        solar energy / vehicle load energy

    Regenerative contribution ratio:
        recovered regenerative energy / vehicle load energy

    These are contribution ratios, not overall thermodynamic efficiency.
    Their sum can exceed 100% if energy is stored, curtailed, or counted
    at different stages. They should not automatically be added together.
    """
    solar = totals.get("solar_energy_kwh")
    regen = totals.get("regenerative_energy_kwh")
    load = totals.get("vehicle_load_energy_kwh")
    losses = totals.get("total_modeled_losses_kwh")

    solar_ratio = None
    regen_ratio = None
    loss_ratio = None

    if load is not None and load > EPSILON:
        if solar is not None:
            solar_ratio = 100.0 * solar / load

        if regen is not None:
            regen_ratio = 100.0 * regen / load

        if losses is not None:
            loss_ratio = 100.0 * losses / load

    return {
        "solar_contribution_percent": solar_ratio,
        "regenerative_contribution_percent": regen_ratio,
        "modeled_losses_as_percent_of_load": loss_ratio,
    }


# ============================================================
# 5. BATTERY-SWITCHING ANALYSIS
# ============================================================

def summarize_switching(
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Summarize battery switching events.

    Handles common event field names. A missing success field is
    classified as unknown rather than automatically successful.
    """
    event_type_column = find_column(
        events,
        ["event_type", "type", "event"],
    )
    success_column = find_column(
        events,
        ["success", "switch_successful", "successful"],
    )
    from_column = find_column(
        events,
        ["from_battery", "source_battery", "previous_battery"],
    )
    to_column = find_column(
        events,
        ["to_battery", "target_battery", "new_battery"],
    )

    switches = []
    for event in events:
        event_type = (
            str(event.get(event_type_column, ""))
            if event_type_column else ""
        )
        normalized_type = event_type.lower()

        # Include explicit switch events and records that identify
        # both a source and a destination battery.
        has_battery_pair = (
            from_column is not None
            and to_column is not None
            and event.get(from_column)
            and event.get(to_column)
        )

        if "switch" in normalized_type or has_battery_pair:
            switches.append(event)

    successes = 0
    failures = 0
    unknown = 0
    transitions = Counter()

    for event in switches:
        if success_column is None:
            unknown += 1
        else:
            value = str(event.get(success_column, "")).strip().lower()

            if value in {"true", "1", "yes", "success"}:
                successes += 1
            elif value in {"false", "0", "no", "failed", "failure"}:
                failures += 1
            else:
                unknown += 1

        if from_column and to_column:
            source = str(event.get(from_column, "")).strip()
            target = str(event.get(to_column, "")).strip()

            if source and target:
                transitions[f"{source} -> {target}"] += 1

    return {
        "total_events": len(events),
        "switch_attempts": len(switches),
        "successful_switches": successes,
        "failed_switches": failures,
        "unknown_switch_outcomes": unknown,
        "switch_success_rate_percent": (
            100.0 * successes / (successes + failures)
            if successes + failures > 0
            else None
        ),
        "transitions": dict(transitions),
    }


# ============================================================
# 6. SCENARIO COMPARISON
# ============================================================

def compare_scenarios(
    scenarios: dict[str, list[dict[str, Any]]],
    scenario_events: dict[str, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    """
    Compare multiple simulation scenarios.

    Example:
        scenarios = {
            "default": default_samples,
            "strategy_a": strategy_a_samples,
            "strategy_b": strategy_b_samples,
        }

    All scenarios should use the same drive profile, duration,
    vehicle parameters, units, and other conditions when the goal
    is to isolate the effect of battery-selection strategy.
    """
    scenario_events = scenario_events or {}
    results = []

    for name, samples in scenarios.items():
        totals = calculate_total_energy(samples)
        efficiency = calculate_efficiency(totals)
        switching = summarize_switching(
            scenario_events.get(name, [])
        )

        results.append({
            "scenario": name,
            **totals,
            **efficiency,
            "switch_attempts": switching["switch_attempts"],
            "successful_switches": switching["successful_switches"],
            "failed_switches": switching["failed_switches"],
            "switch_success_rate_percent":
                switching["switch_success_rate_percent"],
        })

    return results


# ============================================================
# 7. PERFORMANCE REPORT
# ============================================================

def generate_report(
    totals: dict[str, Any],
    efficiency: dict[str, Any],
    switching: dict[str, Any],
    output_path: str | Path = REPORT_FILE,
) -> Path:
    """Generate a readable Markdown performance report."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Fluxxwave EV — Simulation Performance Report",
        "",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "> This report describes simulated results, not validated hardware performance.",
        "",
        "## 1. Energy totals",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]

    display_names = {
        "recorded_steps": "Recorded simulation steps",
        "solar_energy_kwh": "Solar energy",
        "regenerative_energy_kwh": "Regenerative energy recovered",
        "vehicle_load_energy_kwh": "Vehicle load energy",
        "battery_energy_removed_kwh": "Battery energy removed",
        "battery_energy_stored_kwh": "Battery energy stored",
        "battery_charge_loss_kwh": "Battery charging losses",
        "battery_discharge_loss_kwh": "Battery discharging losses",
        "battery_losses_kwh": "Combined battery losses",
        "conversion_loss_kwh": "Other recorded conversion losses",
        "total_modeled_losses_kwh": "Total reported modeled losses",
        "curtailed_energy_kwh": "Curtailed energy",
        "unmet_demand_kwh": "Unmet demand",
    }

    for key, label in display_names.items():
        value = totals.get(key)

        if key.endswith("_kwh") and value is not None:
            value = f"{fmt(value)} kWh"

        lines.append(f"| {label} | {fmt(value) if not isinstance(value, str) else value} |")

    lines.extend([
        "",
        "## 2. Contribution and loss ratios",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Solar contribution relative to load | {fmt(efficiency.get('solar_contribution_percent'))}% |",
        f"| Regenerative contribution relative to load | {fmt(efficiency.get('regenerative_contribution_percent'))}% |",
        f"| Modeled losses relative to load | {fmt(efficiency.get('modeled_losses_as_percent_of_load'))}% |",
        "",
        "These are ratios relative to the recorded vehicle load. They are not a complete thermodynamic efficiency calculation.",
        "",
        "## 3. Battery switching",
        "",
        f"- Total event records: {switching.get('total_events', 0)}",
        f"- Switch attempts: {switching.get('switch_attempts', 0)}",
        f"- Successful switches: {switching.get('successful_switches', 0)}",
        f"- Failed switches: {switching.get('failed_switches', 0)}",
        f"- Unknown outcomes: {switching.get('unknown_switch_outcomes', 0)}",
        f"- Switch success rate: {fmt(switching.get('switch_success_rate_percent'))}%",
        "",
        "### Battery transitions",
        "",
    ])

    transitions = switching.get("transitions", {})

    if transitions:
        for transition, count in sorted(transitions.items()):
            lines.append(f"- {transition}: {count}")
    else:
        lines.append("- No identifiable battery transitions were recorded.")

    lines.extend([
        "",
        "## 4. Interpretation and limitations",
        "",
        "- Missing columns produce unavailable metrics; they are not evidence of zero energy.",
        "- Solar and regenerative energy may be counted at a different system boundary than battery-stored energy.",
        "- Do not add energy totals from different stages of the same energy flow.",
        "- Loss totals are only as complete as the losses explicitly recorded by the simulator.",
        "- Scenario comparisons are meaningful only when operating conditions are comparable.",
        "- Regenerative braking recovers part of vehicle kinetic energy during deceleration; it is not a source of free energy.",
        "",
    ])

    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ============================================================
# 8. GRAPHS
# ============================================================

def generate_graphs(
    totals: dict[str, Any],
    output_path: str | Path = GRAPH_FILE,
) -> Path | None:
    """
    Generate an energy-summary bar chart.

    Matplotlib is optional. If unavailable, the analysis and CSV
    reports still work.
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print(
            "Matplotlib is not installed. "
            "Skipping graphs; CSV and report generation still work."
        )
        return None

    labels = []
    values = []

    metrics = [
        ("Solar", "solar_energy_kwh"),
        ("Regenerative", "regenerative_energy_kwh"),
        ("Vehicle load", "vehicle_load_energy_kwh"),
        ("Battery stored", "battery_energy_stored_kwh"),
        ("Battery removed", "battery_energy_removed_kwh"),
        ("Modeled losses", "total_modeled_losses_kwh"),
    ]

    for label, key in metrics:
        value = totals.get(key)
        if value is not None:
            labels.append(label)
            values.append(value)

    if not values:
        print("No usable energy metrics available for graphing.")
        return None

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(labels, values)
    ax.set_title("Fluxxwave — Recorded Energy Metrics")
    ax.set_ylabel("Energy (kWh)")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)

    return path


# ============================================================
# 9. MAIN ANALYSIS PIPELINE
# ============================================================

def run_analysis(
    samples_file: str | Path = DEFAULT_SAMPLES_FILE,
    events_file: str | Path = DEFAULT_EVENTS_FILE,
    output_directory: str | Path = DEFAULT_OUTPUT_DIRECTORY,
) -> dict[str, Any]:
    """
    Load logged data, calculate metrics, and export analysis outputs.
    """
    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)

    samples = load_csv(samples_file)

    # Events may legitimately be absent if no event file was created.
    events_path = Path(events_file)
    events = load_csv(events_path) if events_path.exists() else []

    totals = calculate_total_energy(samples)
    efficiency = calculate_efficiency(totals)
    switching = summarize_switching(events)

    combined = {
        **totals,
        **efficiency,
        "switch_attempts": switching["switch_attempts"],
        "successful_switches": switching["successful_switches"],
        "failed_switches": switching["failed_switches"],
        "switch_success_rate_percent":
            switching["switch_success_rate_percent"],
    }

    write_csv(output_dir / "summary.csv", [combined])

    write_csv(
        output_dir / "switching_summary.csv",
        [{
            "total_events": switching["total_events"],
            "switch_attempts": switching["switch_attempts"],
            "successful_switches": switching["successful_switches"],
            "failed_switches": switching["failed_switches"],
            "unknown_switch_outcomes": switching["unknown_switch_outcomes"],
            "switch_success_rate_percent":
                switching["switch_success_rate_percent"],
        }],
    )

    report_path = generate_report(
        totals,
        efficiency,
        switching,
        output_dir / "report.md",
    )

    graph_path = generate_graphs(
        totals,
        output_dir / "energy_analysis.png",
    )

    print("\n" + "=" * 55)
    print("FLUXXWAVE PERFORMANCE ANALYSIS")
    print("=" * 55)

    for key, value in combined.items():
        print(f"{key}: {fmt(value) if isinstance(value, float) else value}")

    print("\nOutputs:")
    print(f"- Summary: {output_dir / 'summary.csv'}")
    print(f"- Switching: {output_dir / 'switching_summary.csv'}")
    print(f"- Report: {report_path}")

    if graph_path:
        print(f"- Graph: {graph_path}")

    return {
        "totals": totals,
        "efficiency": efficiency,
        "switching": switching,
        "summary": combined,
        "report_path": report_path,
        "graph_path": graph_path,
    }


def main() -> None:
    """Run analysis using the default Fluxxwave log paths."""
    try:
        run_analysis()
    except FileNotFoundError as error:
        print(f"\nAnalysis could not start:\n{error}")


if __name__ == "__main__":
    main()
