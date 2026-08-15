import subprocess
import time
import json
import argparse
from datetime import datetime

# Fields pulled from nvidia-smi, in order.
QUERY_FIELDS = [
    "utilization.gpu",
    "memory.used",
    "memory.total",
    "temperature.gpu",
    "power.draw",
]

def get_reading():
    """Run nvidia-smi once and return one cleaned reading as a dictionary."""
    query = ",".join(QUERY_FIELDS)
    result = subprocess.run(
        ["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"],
        capture_output=True,
        text=True,
    )

    # nvidia-smi returns something like: "99, 356, 4096, 67, 64.10"
    raw_values = result.stdout.strip().split(",")

    # Pair each field name with its value and convert to a number.
    reading = {"timestamp": datetime.now().isoformat()}
    for field, value in zip(QUERY_FIELDS, raw_values):
        reading[field] = float(value.strip())

    return reading

def collect(duration_seconds=30, interval_seconds=1, output_file="telemetry.json"):
    """Collect readings on a loop and save them all to a JSON file."""
    print(f"Collecting telemetry for {duration_seconds} seconds, "
          f"every {interval_seconds}s...")
    print("-" * 40)

    readings = []
    start_time = time.time()

    while time.time() - start_time < duration_seconds:
        reading = get_reading()
        readings.append(reading)
        # Show a live line so you can watch it work.
        print(f"{reading['timestamp']} | "
              f"GPU {reading['utilization.gpu']:.0f}% | "
              f"Mem {reading['memory.used']:.0f} MiB | "
              f"{reading['temperature.gpu']:.0f}C | "
              f"{reading['power.draw']:.1f}W")
        time.sleep(interval_seconds)

    # Save everything to a JSON file.
    with open(output_file, "w") as f:
        json.dump(readings, f, indent=2)

    print("-" * 40)
    print(f"Collected {len(readings)} readings.")
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GPU telemetry collector.")
    parser.add_argument("--duration", type=int, default=30,
                        help="How many seconds to collect.")
    parser.add_argument("--interval", type=int, default=1,
                        help="Seconds between readings.")
    parser.add_argument("--output", type=str, default="telemetry.json",
                        help="Output JSON file name.")
    args = parser.parse_args()

    collect(duration_seconds=args.duration,
            interval_seconds=args.interval,
            output_file=args.output)