import json
import argparse
import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Import the analysis functions we already built, so we don't duplicate them.
from analyze_telemetry import load_telemetry, summarize, detect_anomalies

# Load the API key from the .env file into the environment.
load_dotenv()

def build_prompt(summary, findings):
    """Turn the diagnostic data into a clear prompt for Claude."""
    # Format the summary stats as readable text.
    summary_text = (
        f"Readings analyzed: {summary['readings_count']}\n"
        f"GPU utilization: avg {summary['avg_utilization']:.0f}%, "
        f"min {summary['min_utilization']:.0f}%, max {summary['max_utilization']:.0f}%\n"
        f"Memory used: avg {summary['avg_memory_used']:.0f} MiB, "
        f"peak {summary['max_memory_used']:.0f} of {summary['memory_total']:.0f} MiB\n"
        f"Temperature: avg {summary['avg_temp']:.0f}C, peak {summary['max_temp']:.0f}C\n"
        f"Power draw: avg {summary['avg_power']:.1f}W, peak {summary['max_power']:.1f}W"
    )

    # Format the findings, or note that there were none.
    if findings:
        findings_text = "\n".join(
            f"- [{f['severity'].upper()}] {f['type']}: {f['message']}"
            for f in findings
        )
    else:
        findings_text = "No automated anomalies were flagged."

    # Assemble the full prompt.
    prompt = f"""You are a GPU QA engineer triaging a diagnostic report from a workload run on an NVIDIA GPU.

Here are the telemetry summary statistics:
{summary_text}

Here are the automated findings from the analysis tool:
{findings_text}

Based on this data, provide a concise triage report with exactly these three sections:

ROOT CAUSE HYPOTHESIS: Your best assessment of what is happening and why, in 2-3 sentences.

TRIAGE PRIORITY: One of P0 (critical), P1 (high), P2 (medium), or P3 (low), followed by a one-sentence justification.

RECOMMENDED NEXT STEP: One concrete action an engineer should take to investigate or resolve this.

Keep the entire response under 200 words and write it in plain, professional language."""

    return prompt

def get_ai_triage(summary, findings):
    """Send the diagnostic data to Claude and return its triage report."""
    client = Anthropic()  # Reads the API key from the environment automatically.

    prompt = build_prompt(summary, findings)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    # The response text is in the content of the returned message.
    return message.content[0].text

def main(path):
    # Reuse our existing analysis pipeline.
    readings = load_telemetry(path)
    summary = summarize(readings)

    if summary is None:
        print("No readings found in telemetry file.")
        return

    findings = detect_anomalies(readings, summary)

    print("=" * 50)
    print("AI TRIAGE REPORT")
    print("=" * 50)
    print(f"Source: {path}")
    print("-" * 50)

    triage = get_ai_triage(summary, findings)
    print(triage)

    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI-powered GPU triage using Claude.")
    parser.add_argument("--input", type=str, default="telemetry.json",
                        help="Telemetry JSON file to triage.")
    args = parser.parse_args()

    main(args.input)