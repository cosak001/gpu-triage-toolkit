import torch
import time
import argparse

def run_gpu_workload(duration_seconds=30, matrix_size=4096):
    """
    Put the GPU under sustained load using repeated matrix multiplication.

    duration_seconds: how long to keep the GPU busy.
    matrix_size: size of the square matrices. Bigger means heavier load.
    """
    # Make sure a GPU is actually available before we start.
    if not torch.cuda.is_available():
        print("No CUDA GPU available. Exiting.")
        return

    device = torch.device("cuda")
    gpu_name = torch.cuda.get_device_name(0)
    print(f"Starting workload on: {gpu_name}")
    print(f"Matrix size: {matrix_size} x {matrix_size}")
    print(f"Target duration: {duration_seconds} seconds")
    print("-" * 40)

    # Create two large random matrices directly on the GPU.
    a = torch.randn(matrix_size, matrix_size, device=device)
    b = torch.randn(matrix_size, matrix_size, device=device)

    start_time = time.time()
    iterations = 0

    # Keep multiplying until the time is up.
    while time.time() - start_time < duration_seconds:
        result = torch.matmul(a, b)
        # This line forces the GPU to actually finish the work
        # before moving on, so the load is real and measurable.
        torch.cuda.synchronize()
        iterations += 1

    elapsed = time.time() - start_time
    print(f"Workload complete.")
    print(f"Iterations performed: {iterations}")
    print(f"Actual duration: {elapsed:.2f} seconds")

if __name__ == "__main__":
    # Let the user set duration and matrix size from the command line.
    parser = argparse.ArgumentParser(description="GPU stress workload.")
    parser.add_argument("--duration", type=int, default=30,
                        help="How many seconds to run.")
    parser.add_argument("--size", type=int, default=4096,
                        help="Matrix dimension.")
    args = parser.parse_args()

    run_gpu_workload(duration_seconds=args.duration, matrix_size=args.size)