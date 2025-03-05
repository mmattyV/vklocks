import re
import os
import statistics

def get_tick_rate(filepath):
    """
    Reads the log file and extracts the tick rate from the initialization line.
    The expected format is:
      "Machine <machine_id> initialized with tick rate <tick_rate> ticks per second"
    Returns the tick rate as an integer if found, or None otherwise.
    """
    pattern = re.compile(r"Machine\s+(\S+)\s+initialized with tick rate (\d+) ticks per second")
    with open(filepath, 'r') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                return int(match.group(2))
    return None

def process_log_file(filepath):
    """
    Parses a log file and extracts events as tuples:
      (logical_clock, system_time, queue_length)
    where queue_length is None if not present.
    """
    events = []
    # Regex pattern matches lines with "updated logical clock to" and captures:
    # the clock value, the system_time, and optionally the queue_length.
    pattern = re.compile(r"updated logical clock to (\d+), system_time=(\d+)(?:, queue_length=(\d+))?")
    with open(filepath, 'r') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                logical_clock = int(match.group(1))
                system_time = int(match.group(2))
                queue_length = int(match.group(3)) if match.group(3) is not None else None
                events.append((logical_clock, system_time, queue_length))
    return events

def compute_jumps(events):
    """Computes the differences (jumps) between consecutive logical clock values."""
    jumps = []
    # Ensure events are sorted by system_time.
    events.sort(key=lambda x: x[1])
    for i in range(1, len(events)):
        jump = events[i][0] - events[i-1][0]
        jumps.append(jump)
    return jumps

def analyze_run(run_dir, machine_ids):
    """Analyzes the log files in a given run directory and prints statistics."""
    print(f"\nStatistics for run: {run_dir}")
    drift_end = {}
    for machine in machine_ids:
        logfile = os.path.join(run_dir, f"{machine}_log.txt")
        if not os.path.exists(logfile):
            continue
        # Get the tick rate (clock cycle value) from the initialization line.
        tick_rate = get_tick_rate(logfile)
        events = process_log_file(logfile)
        jumps = compute_jumps(events)
        if jumps:
            avg_jump = statistics.mean(jumps)
            max_jump = max(jumps)
            min_jump = min(jumps)
            std_jump = statistics.stdev(jumps) if len(jumps) > 1 else 0
        else:
            avg_jump = max_jump = min_jump = std_jump = 0

        # Get the final logical clock value.
        final_value = events[-1][0] if events else 0
        drift_end[machine] = final_value

        # Compute average queue length for events that include a queue_length.
        queue_lengths = [e[2] for e in events if e[2] is not None]
        avg_queue = statistics.mean(queue_lengths) if queue_lengths else 0

        print(f"  {machine}:")
        if tick_rate is not None:
            print(f"    Clock cycle (tick rate): {tick_rate} ticks per second")
        else:
            print("    Clock cycle (tick rate): Not found")
        print(f"    Final logical clock: {final_value}")
        print(f"    Jump sizes: avg = {avg_jump:.2f}, min = {min_jump}, max = {max_jump}, std = {std_jump:.2f}")
        print(f"    Average message queue length: {avg_queue:.2f}")

    if drift_end:
        drift = max(drift_end.values()) - min(drift_end.values())
        print(f"  Drift between machines (final clock difference): {drift}\n")
    else:
        print("  No data available.\n")

def main():
    # List of run directories and machine IDs.
    runs = [f"experiments/experiment_run_{i}" for i in range(1, 6)]
    machine_ids = ["machine1", "machine2", "machine3", "machine4"]

    for run in runs:
        if os.path.isdir(run):
            analyze_run(run, machine_ids)
        else:
            print(f"Run directory {run} does not exist.")

if __name__ == "__main__":
    main()