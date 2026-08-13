import subprocess

def get_gpu_name(_):
    "Run nvidia_smi and pullout GPU name."
    result = subprocess.run( ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], 
                            capture_output = True, 
                            text = True
    )
    return result.stdout.strip()
if __name__ == "__main__":
    gpu =get_gpu_name()
    print(f"Detected GPU: {gpu}")

