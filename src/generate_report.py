import json
import argparse
import os
from datetime import datetime

# Reuse everything we already built.
from analyze_telemetry import load_telemetry, summarize, detect_anomalies
from ai_triage import get_ai_triage

def build_report_data(path):
    """Run the full pipeline and assemble all results into one dictionary."""
    readings = load_telemetry(path)
    summary = summarize(readings)

    if summary is None:
        return None

    findings = detect_anomalies(readings, summary)

    # Get the AI triage. Wrapped in try/except so a failed API call
    # doesn't crash the whole report.
    try:
        ai_triage = get_ai_triage(summary, findings)
    except Exception as e:
        ai_triage = f"AI triage unavailable: {e}"

    # Assemble everything into one structured record.
    report = {
        "generated_at": datetime.now().isoformat(),
        "source_file": path,
        "summary": summary,
        "findings": findings,
        "ai_triage": ai_triage,
    }
    return report

def write_json_report(report, output_path):
    """Save the report as structured JSON."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

def write_markdown_report(report, output_path):
    """Save the report as a human-readable Markdown file."""
    summary = report["summary"]
    findings = report["findings"]

    lines = []
    lines.append("# GPU Diagnostic Report")
    lines.append("")
    lines.append(f"**Generated:** {report['generated_at']}")
    lines.append(f"**Source telemetry:** {report['source_file']}")
    lines.append("")

    lines.append("## Telemetry Summary")
    lines.append("")
    lines.append(f"- Readings analyzed: {summary['readings_count']}")
    lines.append(f"- GPU utilization: avg {summary['avg_utilization']:.0f}%, "
                 f"min {summary['min_utilization']:.0f}%, "
                 f"max {summary['max_utilization']:.0f}%")
    lines.append(f"- Memory used: avg {summary['avg_memory_used']:.0f} MiB, "
                 f"peak {summary['max_memory_used']:.0f} of "
                 f"{summary['memory_total']:.0f} MiB")
    lines.append(f"- Temperature: avg {summary['avg_temp']:.0f}C, "
                 f"peak {summary['max_temp']:.0f}C")
    lines.append(f"- Power draw: avg {summary['avg_power']:.1f}W, "
                 f"peak {summary['max_power']:.1f}W")
    lines.append("")

    lines.append("## Automated Findings")
    lines.append("")
    if findings:
        for f in findings:
            lines.append(f"- **[{f['severity'].upper()}] {f['type']}**: {f['message']}")
    else:
        lines.append("- No anomalies detected. Workload appears healthy.")
    lines.append("")

    lines.append("## AI Triage Report")
    lines.append("")
    lines.append(report["ai_triage"])
    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

def main(path):
    # Check the input file exists before doing anything.
    if not os.path.exists(path):
        print(f"Error: telemetry file not found: {path}")
        return

    print(f"Generating report from {path}...")

    report = build_report_data(path)
    if report is None:
        print("No readings found in telemetry file. Nothing to report.")
        return

    # Build output filenames with a timestamp so reports don't overwrite.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = f"report_{timestamp}.json"
    md_path = f"report_{timestamp}.md"

    write_json_report(report, json_path)
    write_markdown_report(report, md_path)

    print(f"Saved JSON report:     {json_path}")
    print(f"Saved Markdown report: {md_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a full GPU diagnostic report.")
    parser.add_argument("--input", type=str, default="telemetry.json",
                        help="Telemetry JSON file to report on.")
    args = parser.parse_args()

    main(args.input)