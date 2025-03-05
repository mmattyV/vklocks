import re
import os
import datetime
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict, Counter

class LogAnalyzer:
    def __init__(self, log_dir='.', experiment_name=None):
        self.log_dir = log_dir
        self.experiment_name = experiment_name
        
        # If experiment name is provided, use it to identify log files
        if experiment_name:
            self.log_files = [f for f in os.listdir(log_dir) if f.startswith(f'machine_') and f.endswith('.log') and experiment_name in f]
        else:
            self.log_files = [f for f in os.listdir(log_dir) if f.startswith('machine_') and f.endswith('.log')]
        
        self.log_files.sort()  # Sort by machine ID
        
        # Regular expressions for parsing log entries
        self.timestamp_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d+)'
        self.event_pattern = r'(SEND|RECEIVE|INTERNAL)'
        self.clock_pattern = r'Logical Clock: (\d+)'
        self.queue_pattern = r'Queue Length: (\d+)'
        self.sender_pattern = r'From: Machine (\d+)'
        self.destination_pattern = r'Destination: Machine at \([\'"]?localhost[\'"]?, (\d+)\)'
        
        # Data structures to hold parsed log information
        self.events = defaultdict(list)  # Machine ID -> list of event dictionaries
        self.logical_clocks = defaultdict(list)  # Machine ID -> list of (timestamp, clock_value) tuples
        self.queue_lengths = defaultdict(list)  # Machine ID -> list of (timestamp, queue_length) tuples
        self.clock_jumps = defaultdict(list)  # Machine ID -> list of jump values
        self.communication = defaultdict(lambda: defaultdict(int))  # (from_id, to_id) -> count
        
    def parse_logs(self):
        """Parse all log files and extract relevant information."""
        for log_file in self.log_files:
            machine_id = int(log_file.split('_')[1].split('.')[0])
            
            # List to store events for this machine
            machine_events = []
            
            with open(os.path.join(self.log_dir, log_file), 'r') as f:
                for line in f:
                    # Extract timestamp
                    timestamp_match = re.search(self.timestamp_pattern, line)
                    if not timestamp_match:
                        continue
                    timestamp_str = timestamp_match.group(1)
                    timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
                    
                    # Extract event type
                    event_match = re.search(self.event_pattern, line)
                    if not event_match:
                        continue
                    event_type = event_match.group(1)
                    
                    # Extract logical clock
                    clock_match = re.search(self.clock_pattern, line)
                    if not clock_match:
                        continue
                    logical_clock = int(clock_match.group(1))
                    
                    # Create event dictionary
                    event = {
                        'timestamp': timestamp,
                        'type': event_type,
                        'logical_clock': logical_clock
                    }
                    
                    # Add sender information for RECEIVE events
                    if event_type == 'RECEIVE':
                        sender_match = re.search(self.sender_pattern, line)
                        if sender_match:
                            sender_id = int(sender_match.group(1))
                            event['sender_id'] = sender_id
                            # Record communication pattern
                            self.communication[sender_id][machine_id] += 1
                        
                        # Add queue length for RECEIVE events
                        queue_match = re.search(self.queue_pattern, line)
                        if queue_match:
                            queue_length = int(queue_match.group(1))
                            event['queue_length'] = queue_length
                            self.queue_lengths[machine_id].append((timestamp, queue_length))
                    
                    # Add destination information for SEND events
                    elif event_type == 'SEND':
                        dest_match = re.search(self.destination_pattern, line)
                        if dest_match:
                            dest_port = int(dest_match.group(1))
                            # Convert port to machine ID (assuming port = 50000 + machine_id)
                            dest_id = dest_port - 50000
                            event['destination_id'] = dest_id
                    
                    # Add event to the list for this machine
                    machine_events.append(event)
                    self.logical_clocks[machine_id].append((timestamp, logical_clock))
            
            # Sort events by timestamp (chronological order)
            machine_events.sort(key=lambda e: e['timestamp'])
            
            # Store sorted events
            self.events[machine_id] = machine_events
            
            # Calculate jumps for this machine based on chronological order
            self.calculate_clock_jumps_for_machine(machine_id, machine_events)
    
    def calculate_clock_jumps_for_machine(self, machine_id, events):
        """Calculate jumps in logical clock values for a single machine, using events in chronological order."""
        if not events or len(events) < 2:
            return
            
        # Process events in chronological order
        for i in range(1, len(events)):
            prev_clock = events[i-1]['logical_clock']
            curr_clock = events[i]['logical_clock']
            
            # Calculate jump
            jump = curr_clock - prev_clock
            
            # Logical clocks should always increment
            if jump > 0:
                self.clock_jumps[machine_id].append(jump)
            # If jump is 0 or negative, this is likely a log parsing issue or out-of-order events
            # We'll log these as warnings but won't include them in analysis
            elif jump <= 0:
                print(f"Warning: Non-positive clock jump detected in Machine {machine_id}: " +
                      f"From {prev_clock} to {curr_clock} at {events[i]['timestamp']}")
    
    def analyze_clock_jumps(self):
        """Analyze the jumps in logical clock values."""
        print("\n=== Logical Clock Jumps Analysis ===")
        for machine_id, jumps in self.clock_jumps.items():
            if jumps:
                avg_jump = sum(jumps) / len(jumps)
                max_jump = max(jumps)
                min_jump = min(jumps)
                print(f"Machine {machine_id}:")
                print(f"  Average jump: {avg_jump:.2f}")
                print(f"  Maximum jump: {max_jump}")
                print(f"  Minimum jump: {min_jump}")
                
                # Count occurrences of each jump value
                jump_counter = Counter(jumps)
                most_common_jumps = jump_counter.most_common(3)
                print(f"  Most common jumps: {most_common_jumps}")
                print()
    
    def find_clock_at_time(self, machine_id, target_time, window_ms=100):
        """Find the logical clock value closest to the target time within a window."""
        window = datetime.timedelta(milliseconds=window_ms)
        best_match = None
        min_diff = datetime.timedelta.max
        
        for time, clock in self.logical_clocks[machine_id]:
            diff = abs(time - target_time)
            if diff < window and diff < min_diff:
                min_diff = diff
                best_match = clock
                
        return best_match
    
    def analyze_clock_drift(self):
        """Analyze the drift between logical clocks of different machines."""
        print("\n=== Logical Clock Drift Analysis ===")
        
        # Get the list of all timestamps from all machines
        all_timestamps = []
        for machine_id, clock_data in self.logical_clocks.items():
            all_timestamps.extend([ts for ts, _ in clock_data])
        
        # Remove duplicates and sort
        all_timestamps = sorted(set(all_timestamps))
        
        if not all_timestamps:
            print("No timestamp data available for analysis.")
            return
        
        # Define time window for comparison (in milliseconds)
        window_ms = 100
        
        # Calculate drift between each pair of machines
        machine_ids = sorted(self.logical_clocks.keys())
        for i in range(len(machine_ids)):
            for j in range(i+1, len(machine_ids)):
                machine1 = machine_ids[i]
                machine2 = machine_ids[j]
                
                drifts = []
                # Sample timestamps at regular intervals to avoid too much data
                sample_size = min(100, len(all_timestamps))
                step = max(1, len(all_timestamps) // sample_size)
                
                for k in range(0, len(all_timestamps), step):
                    if k >= len(all_timestamps):
                        break
                        
                    time_point = all_timestamps[k]
                    clock1 = self.find_clock_at_time(machine1, time_point, window_ms)
                    clock2 = self.find_clock_at_time(machine2, time_point, window_ms)
                    
                    if clock1 is not None and clock2 is not None:
                        drift = abs(clock1 - clock2)
                        drifts.append(drift)
                
                if drifts:
                    avg_drift = sum(drifts) / len(drifts)
                    max_drift = max(drifts)
                    min_drift = min(drifts)
                    print(f"Drift between Machine {machine1} and Machine {machine2}:")
                    print(f"  Average drift: {avg_drift:.2f}")
                    print(f"  Maximum drift: {max_drift}")
                    print(f"  Minimum drift: {min_drift}")
                    print(f"  Number of comparison points: {len(drifts)}")
                    print()
    
    def analyze_queue_lengths(self):
        """Analyze message queue lengths."""
        print("\n=== Message Queue Analysis ===")
        for machine_id, queue_data in self.queue_lengths.items():
            if queue_data:
                queue_lengths = [length for _, length in queue_data]
                avg_length = sum(queue_lengths) / len(queue_lengths)
                max_length = max(queue_lengths)
                print(f"Machine {machine_id}:")
                print(f"  Average queue length: {avg_length:.2f}")
                print(f"  Maximum queue length: {max_length}")
                print(f"  Queue length distribution: {Counter(queue_lengths).most_common(5)}")
                print()
    
    def analyze_event_distribution(self):
        """Analyze the distribution of event types."""
        print("\n=== Event Type Distribution ===")
        for machine_id, events in self.events.items():
            event_types = [e['type'] for e in events]
            event_counts = Counter(event_types)
            total_events = len(event_types)
            
            print(f"Machine {machine_id}:")
            for event_type, count in event_counts.items():
                percentage = (count / total_events) * 100
                print(f"  {event_type}: {count} ({percentage:.2f}%)")
            print(f"  Total events: {total_events}")
            print()
    
    def analyze_clock_progress_rate(self):
        """Analyze how fast logical clocks progress relative to system time."""
        print("\n=== Logical Clock Progress Rate Analysis ===")
        
        for machine_id, clock_data in self.logical_clocks.items():
            if len(clock_data) < 2:
                continue
                
            # Sort by system timestamp
            clock_data_sorted = sorted(clock_data)
            
            # Calculate clock rate (logical ticks per second of system time)
            start_time, start_clock = clock_data_sorted[0]
            end_time, end_clock = clock_data_sorted[-1]
            
            time_diff = (end_time - start_time).total_seconds()
            clock_diff = end_clock - start_clock
            
            if time_diff > 0:
                rate = clock_diff / time_diff
                print(f"Machine {machine_id}:")
                print(f"  Logical clock progress rate: {rate:.2f} ticks/second")
                print(f"  Total logical time elapsed: {clock_diff}")
                print(f"  Total system time elapsed: {time_diff:.2f} seconds")
                print()
    
    def analyze_communication_pattern(self):
        """Analyze the communication patterns between machines."""
        print("\n=== Communication Pattern Analysis ===")
        
        for sender_id, receivers in self.communication.items():
            print(f"Machine {sender_id} sent messages to:")
            total_sent = sum(receivers.values())
            for receiver_id, count in receivers.items():
                percentage = (count / total_sent) * 100 if total_sent > 0 else 0
                print(f"  Machine {receiver_id}: {count} messages ({percentage:.2f}%)")
            print()
    
    def plot_logical_clocks(self, save_path=None):
        """Plot logical clock values over time for all machines."""
        plt.figure(figsize=(12, 8))
        
        for machine_id, clock_data in self.logical_clocks.items():
            if not clock_data:
                continue
                
            # Sort by timestamp
            clock_data = sorted(clock_data)
            timestamps, clock_values = zip(*clock_data)
            
            # Convert timestamps to seconds from start
            all_start_times = [min(ts for ts, _ in data) for machine_id, data in self.logical_clocks.items() if data]
            if not all_start_times:
                continue
                
            start_time = min(all_start_times)
            seconds = [(ts - start_time).total_seconds() for ts in timestamps]
            
            plt.plot(seconds, clock_values, label=f"Machine {machine_id}")
        
        plt.xlabel("Time (seconds)")
        plt.ylabel("Logical Clock Value")
        plt.title("Logical Clock Values Over Time")
        plt.legend()
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
    
    def plot_queue_lengths(self, save_path=None):
        """Plot message queue lengths over time for all machines."""
        plt.figure(figsize=(12, 8))
        
        for machine_id, queue_data in self.queue_lengths.items():
            if not queue_data:
                continue
                
            # Sort by timestamp
            queue_data = sorted(queue_data)
            timestamps, lengths = zip(*queue_data)
            
            # Convert timestamps to seconds from start
            all_start_times = []
            for m_id, data in self.queue_lengths.items():
                if data:
                    all_start_times.append(min(ts for ts, _ in data))
            
            if not all_start_times:
                continue
                
            start_time = min(all_start_times)
            seconds = [(ts - start_time).total_seconds() for ts in timestamps]
            
            plt.plot(seconds, lengths, label=f"Machine {machine_id}")
        
        plt.xlabel("Time (seconds)")
        plt.ylabel("Queue Length")
        plt.title("Message Queue Lengths Over Time")
        plt.legend()
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()
    
    def run_analysis(self, plot=True, save_plots=False):
        """Run all analyses."""
        print(f"Analyzing logs{f' for experiment: {self.experiment_name}' if self.experiment_name else ''}...")
        
        self.parse_logs()
        self.analyze_event_distribution()
        self.analyze_clock_jumps()
        self.analyze_clock_drift()
        self.analyze_queue_lengths()
        self.analyze_clock_progress_rate()
        self.analyze_communication_pattern()
        
        if plot:
            if save_plots:
                plot_dir = "plots"
                os.makedirs(plot_dir, exist_ok=True)
                
                exp_suffix = f"_{self.experiment_name}" if self.experiment_name else ""
                self.plot_logical_clocks(os.path.join(plot_dir, f"logical_clocks{exp_suffix}.png"))
                self.plot_queue_lengths(os.path.join(plot_dir, f"queue_lengths{exp_suffix}.png"))
            else:
                self.plot_logical_clocks()
                self.plot_queue_lengths()

if __name__ == "__main__":
    analyzer = LogAnalyzer()
    analyzer.run_analysis()