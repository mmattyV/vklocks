import subprocess
import time
import os
import shutil

# Number of experiment runs and duration (in seconds) per run.
NUM_RUNS = 5
RUN_DURATION = 60  # one minute per run

# Experiment parameters to modify clock cycles and tight mode.
EXPERIMENT_MIN_TICKS = 1  # Minimum ticks per second for the experiment
EXPERIMENT_MAX_TICKS = 2  # Maximum ticks per second for the experiment
EXPERIMENT_TIGHT = True   # Enable tight mode (smaller probability of internal events)

# Configuration for the three virtual machines.
# Each tuple: (machine_id, port, comma-separated peer addresses)
VM_CONFIGS = [
    ('machine1', '50051', 'localhost:50052,localhost:50053'),
    ('machine2', '50052', 'localhost:50051,localhost:50053'),
    ('machine3', '50053', 'localhost:50051,localhost:50052'),
]

def run_experiment():
    """Launches the three VM processes with the modified tick rate and tight mode parameters,
    lets them run for RUN_DURATION seconds, then terminates the processes."""
    processes = []

    # Launch each VM as a subprocess.
    for machine_id, port, peers in VM_CONFIGS:
        cmd = [
            'python', 'virtual_machine.py', machine_id, port, peers,
            '--min-ticks', str(EXPERIMENT_MIN_TICKS),
            '--max-ticks', str(EXPERIMENT_MAX_TICKS)
        ]
        if EXPERIMENT_TIGHT:
            cmd.append('--tight')
        print(f"Starting {machine_id} on port {port} with peers {peers}")
        print("Command:", " ".join(cmd))
        proc = subprocess.Popen(cmd)
        processes.append(proc)

    # Let the VMs run for the specified duration.
    time.sleep(RUN_DURATION)

    # Terminate all VM processes.
    print("Terminating VM processes for this run...")
    for proc in processes:
        proc.terminate()
    # Allow a few seconds for clean termination.
    time.sleep(5)

def collect_logs(run_number):
    """Moves log files into a directory specific to the current run."""
    run_dir = f"experiment_run_{run_number}"
    os.makedirs(run_dir, exist_ok=True)

    for machine_id, _, _ in VM_CONFIGS:
        log_file = f"{machine_id}_log.txt"
        if os.path.exists(log_file):
            dest = os.path.join(run_dir, log_file)
            shutil.move(log_file, dest)
            print(f"Moved {log_file} to {run_dir}")

if __name__ == "__main__":
    print("Experiment parameters:")
    print("  Run duration:", RUN_DURATION, "seconds per run")
    print("  Number of runs:", NUM_RUNS)
    print("  Tick rate range:", EXPERIMENT_MIN_TICKS, "to", EXPERIMENT_MAX_TICKS, "ticks per second")
    print("  Tight mode:", "Enabled" if EXPERIMENT_TIGHT else "Disabled")
    for run in range(1, NUM_RUNS + 1):
        print(f"\n=== Starting Experiment Run {run} ===")
        run_experiment()
        collect_logs(run)
        print(f"=== Experiment Run {run} Complete ===\n")
        # Optionally, pause between runs.
        time.sleep(10)