# GPU Diagnostic and Bug Triage Toolkit

An automated pipeline for reproducing GPU workloads, capturing hardware telemetry, detecting performance anomalies, and generating AI-assisted triage reports for NVIDIA GPUs.

## The Problem

When a GPU workload underperforms, fails, or behaves inconsistently on a given machine, an engineer has to reproduce the issue, collect the right diagnostics, decide what actually went wrong, and communicate it clearly. Done by hand, this is slow and inconsistent. This toolkit automates that workflow end to end: it generates a reproducible load, records how the GPU behaves second by second, flags concerning conditions against defined thresholds, and produces a structured triage report with a root-cause hypothesis and severity rating.

## What It Does

The toolkit runs as a five-stage pipeline:

1. **Reproduce** — Generate a controlled, configurable GPU workload to create a measurable load.
2. **Collect** — Capture GPU telemetry (utilization, memory, temperature, power) once per second and save it as structured JSON.
3. **Analyze** — Evaluate the telemetry against calibrated thresholds and flag anomalies such as memory pressure, thermal throttling risk, utilization stalls, and power limiting.
4. **Triage** — Send the diagnostic findings to an LLM (Claude) to generate a plain-language root-cause hypothesis, a priority rating (P0–P3), and a recommended next step.
5. **Report** — Combine everything into timestamped diagnostic reports in both machine-readable JSON and human-readable Markdown.

## Example Output

A run against a memory-stressed workload produces a report like this:

> **[HIGH] memory_pressure**: Peak memory reached 96.4% of total (3948 of 4096 MiB). Risk of out-of-memory errors.
>
> **AI Triage — Priority P1 (High):** The workload is sustaining 100% GPU utilization while consuming 96.4% of available VRAM, leaving only ~148 MiB of headroom. Any allocation spike beyond current peak will trigger an out-of-memory error.

See [`samples/sample_report.md`](samples/sample_report.md) for a full example report, and the `samples/` folder for the telemetry data behind it.

## Project Structure

```
gpu-triage-toolkit/
├── src/                      # Core diagnostic pipeline
│   ├── gpu_workload.py       # Generates a configurable GPU load
│   ├── collect_telemetry.py  # Captures GPU telemetry to JSON
│   ├── analyze_telemetry.py  # Detects anomalies against thresholds
│   ├── ai_triage.py          # Generates AI root-cause analysis via Claude
│   └── generate_report.py    # Produces final JSON + Markdown reports
├── utils/                    # Setup verification utilities
│   ├── check_gpu.py          # Confirms nvidia-smi is accessible
│   └── gpu_check.py          # Confirms PyTorch + CUDA see the GPU
├── samples/                  # Example telemetry and a sample report
├── requirements.txt          # Python dependencies
└── README.md
```

## How to Run

**Prerequisites:** An NVIDIA GPU with drivers installed (provides `nvidia-smi`), Python 3.10+, and an Anthropic API key for the AI triage stage.

1. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Add your Anthropic API key to a `.env` file in the project root:

   ```
   ANTHROPIC_API_KEY=your-key-here
   ```

3. Verify your environment:

   ```
   python utils/gpu_check.py
   ```

4. Generate a workload and collect telemetry (in two terminals):

   ```
   python src/gpu_workload.py --duration 45
   python src/collect_telemetry.py --duration 30 --output telemetry.json
   ```

5. Produce a full diagnostic report:

   ```
   python src/generate_report.py --input telemetry.json
   ```

## Key Design Decisions

- **Hardware-adaptive monitoring:** Reads each GPU's actual power limit from `nvidia-smi` and handles missing telemetry without interrupting the pipeline.
- **Modular design:** Each stage is reusable, allowing later components to build on earlier functionality without duplicating code.
- **Validated anomaly detection:** Detection logic was tested by intentionally creating a high-memory GPU workload and confirming the correct severity was reported.

## Skills Demonstrated

- Python scripting and automation (subprocess, JSON, argparse, exception handling)
- GPU telemetry collection and diagnostics using NVIDIA `nvidia-smi`
- PyTorch and CUDA for GPU workload generation
- Threshold-based anomaly detection and root-cause analysis
- LLM integration for AI-assisted tooling (Anthropic Claude API)
- Secure handling of secrets via environment variables
- Clean project structure and version control with Git

## Future Extensions

- **Virtualization support.** Run the same pipeline inside virtualized environments (VMware ESXi, Citrix Hypervisor, Microsoft Hyper-V, KVM) to validate GPU behavior on virtual platforms and compare passthrough performance against bare metal.
- **GPU passthrough diagnostics.** Detect and report which physical GPU a virtualized workload is actually bound to.
- **Continuous monitoring mode.** Run telemetry collection as a background service with alerting on threshold breaches.
- **Configurable thresholds.** Move detection thresholds into a config file for per-GPU tuning.
