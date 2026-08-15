import json
import argparse

# Thresholds that define "concerning" behavior.
# These are engineering judgments and can be tuned.
MEMORY_PRESSURE_PCT = 90.0      # memory used above this % of total
HIGH_TEMP_C = 80.0              # temperature above this risks throttling
LOW_UTIL_PCT = 50.0             # utilization below this during a workload is suspicious
POWER_LIMIT_PCT = 98.0          # power draw above this % of cap means power-limited

def load_telemetry(path):
    """Read the telemetry JSON file into a list of readings."""
    with open(path, "r") as f:
        return json.load(f)

def summarize(readings):
    """Compute basic statistics across all readings."""
    count = len(readings)
    if count == 0:
        return None

    util_values = [r["utilization.gpu"] for r in readings]
    mem_values = [r["memory.used"] for r in readings]
    temp_values = [r["temperature.gpu"] for r in readings]
    power_values = [r["power.draw"] for r in readings]
    mem_total = readings[0]["memory.total"]
    power_cap = readings[0]["power.limit"]

    return {
        "readings_count": count,
        "avg_utilization": sum(util_values) / count,
        "max_utilization": max(util_values),
        "min_utilization": min(util_values),
        "avg_memory_used": sum(mem_values) / count,
        "max_memory_used": max(mem_values),
        "memory_total": mem_total,
        "avg_temp": sum(temp_values) / count,
        "max_temp": max(temp_values),
        "avg_power": sum(power_values) / count,
        "max_power": max(power_values),
        "power_cap": power_cap,
    }

def detect_anomalies(readings, summary):
    """Check the summary against thresholds and return a list of findings."""
    findings = []

    # Memory pressure check.
    mem_pct = (summary["max_memory_used"] / summary["memory_total"]) * 100
    if mem_pct >= MEMORY_PRESSURE_PCT:
        findings.append({
            "severity": "high",
            "type": "memory_pressure",
            "message": f"Peak memory reached {mem_pct:.1f}% of total "
                       f"({summary['max_memory_used']:.0f} of "
                       f"{summary['memory_total']:.0f} MiB). Risk of out-of-memory errors."
        })

    # Thermal check.
    if summary["max_temp"] >= HIGH_TEMP_C:
        findings.append({
            "severity": "high",
            "type": "thermal",
            "message": f"Peak temperature hit {summary['max_temp']:.0f}C, "
                       f"above the {HIGH_TEMP_C:.0f}C throttling-risk threshold."
        })

    # Utilization stall check.
    if summary["min_utilization"] < LOW_UTIL_PCT:
        findings.append({
            "severity": "medium",
            "type": "utilization_stall",
            "message": f"Utilization dropped to {summary['min_utilization']:.0f}% "
                       f"at some point, below the {LOW_UTIL_PCT:.0f}% floor. "
                       f"Possible stall or workload not fully using the GPU."
        })

    # Power limit check.
    # Only run this if the GPU actually reported a power cap.
    # Some laptop GPUs report power.limit as unavailable.
    if summary["power_cap"] is not None:
        power_pct = (summary["max_power"] / summary["power_cap"]) * 100
        if power_pct >= POWER_LIMIT_PCT:
            findings.append({
                "severity": "info",
                "type": "power_limited",
                "message": f"Power draw reached {power_pct:.1f}% of the "
                           f"{summary['power_cap']:.0f}W cap. GPU is power-limited; "
                           f"performance may be capped by the power ceiling."
            })

    return findings

def main(path):
    readings = load_telemetry(path)
    summary = summarize(readings)

    if summary is None:
        print("No readings found in telemetry file.")
        return

    print("=" * 50)
    print("TELEMETRY ANALYSIS")
    print("=" * 50)
    print(f"Readings analyzed: {summary['readings_count']}")
    print(f"Utilization: avg {summary['avg_utilization']:.0f}%, "
          f"min {summary['min_utilization']:.0f}%, "
          f"max {summary['max_utilization']:.0f}%")
    print(f"Memory used: avg {summary['avg_memory_used']:.0f} MiB, "
          f"max {summary['max_memory_used']:.0f} of "
          f"{summary['memory_total']:.0f} MiB")
    print(f"Temperature: avg {summary['avg_temp']:.0f}C, "
          f"max {summary['max_temp']:.0f}C")
    print(f"Power: avg {summary['avg_power']:.1f}W, "
          f"max {summary['max_power']:.1f}W")
    print("-" * 50)

    findings = detect_anomalies(readings, summary)

    if not findings:
        print("No anomalies detected. Workload appears healthy.")
    else:
        print(f"{len(findings)} finding(s):")
        for f in findings:
            print(f"  [{f['severity'].upper()}] {f['type']}: {f['message']}")

    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze GPU telemetry for anomalies.")
    parser.add_argument("--input", type=str, default="telemetry.json",
                        help="Telemetry JSON file to analyze.")
    args = parser.parse_args()

    main(args.input)