import random
import time
import multiprocessing
import subprocess
import os
import sys
from virtual_machine import VirtualMachine

def run_machine(machine_id, clock_rate, port, other_machines, duration, internal_prob):
    """Function to run in a separate process for each virtual machine."""
    vm = VirtualMachine(machine_id, clock_rate, port, other_machines, internal_prob)
    print(f"Starting Machine {machine_id} with clock rate {clock_rate} ticks/sec, internal probability {internal_prob}")
    vm.run(duration)

def setup_system(num_machines=3, duration_seconds=60, min_clock_rate=1, max_clock_rate=6, internal_prob=0.7):
    """
    Set up and run a distributed system with multiple virtual machines.
    
    Args:
        num_machines (int): Number of virtual machines to create
        duration_seconds (int): How long to run the simulation in seconds
        min_clock_rate (int): Minimum clock ticks per second
        max_clock_rate (int): Maximum clock ticks per second
        internal_prob (float): Probability of an internal event
    """
    # Set up ports for each machine
    base_port = 50000  # Higher port numbers to avoid conflicts
    ports = [base_port + i for i in range(1, num_machines + 1)]
    
    # Set up clock rates for each machine
    clock_rates = [random.randint(min_clock_rate, max_clock_rate) for _ in range(num_machines)]
    
    print("=== System Configuration ===")
    for i in range(num_machines):
        print(f"Machine {i+1}: Clock Rate = {clock_rates[i]} ticks/sec, Port = {ports[i]}")
    
    # Create the list of other machines for each machine
    other_machines_list = []
    for i in range(num_machines):
        others = []
        for j in range(num_machines):
            if i != j:
                others.append(('localhost', ports[j]))
        other_machines_list.append(others)
    
    # Create processes for each machine
    processes = []
    for i in range(num_machines):
        p = multiprocessing.Process(
            target=run_machine, 
            args=(i+1, clock_rates[i], ports[i], other_machines_list[i], duration_seconds, internal_prob)
        )
        processes.append(p)
    
    # Start all processes
    for p in processes:
        p.start()
        # Small delay to ensure machines start up in order
        time.sleep(0.5)
    
    print(f"All machines started. Running for {duration_seconds} seconds...")
    
    # Wait for all processes to finish
    for p in processes:
        p.join()
    
    print("All machines have completed their runs.")

def run_experiments():
    """Run the specified experiments for the assignment."""
    print("=== Experiment 1: Standard Configuration (5 runs of 1 minute each) ===")
    for run in range(1, 6):
        print(f"\nStarting Run {run}/5...")
        setup_system(num_machines=3, duration_seconds=60, min_clock_rate=1, max_clock_rate=6)
        print(f"Run {run} completed.")
        time.sleep(2)  # Short pause between runs
    
    print("\n=== Experiment 2: Smaller Variation in Clock Cycles ===")
    setup_system(num_machines=3, duration_seconds=60, min_clock_rate=3, max_clock_rate=4)
    
    print("\n=== Experiment 3: Smaller Probability of Internal Events ===")
    setup_system(num_machines=3, duration_seconds=60, min_clock_rate=1, max_clock_rate=6, internal_prob=0.4)
    
    print("\n=== Experiment 4: Combined Small Variation and Low Internal Probability ===")
    setup_system(num_machines=3, duration_seconds=60, min_clock_rate=3, max_clock_rate=4, internal_prob=0.4)
    
    print("All experiments completed.")

def generate_proto_code():
    """Generate Python code from the .proto file."""
    try:
        # Check if the proto file exists
        if not os.path.exists('clock.proto'):
            print("Proto file not found. Creating it...")
            with open('clock.proto', 'w') as f:
                f.write("""syntax = "proto3";

package distributed_clock;

// Define the clock service
service ClockService {
  // Send a message containing logical clock time
  rpc SendMessage (ClockMessage) returns (ClockResponse) {}
}

// Message containing logical clock time
message ClockMessage {
  int32 sender_id = 1;       // ID of sending machine
  int32 logical_clock = 2;   // Logical clock value
  string timestamp = 3;      // System timestamp for logging
}

// Response after receiving a message
message ClockResponse {
  bool received = 1;         // Acknowledge receipt
}
""")
        
        # Generate Python code from the proto file
        print("Generating gRPC code from proto file...")
        subprocess.check_call([
            sys.executable, '-m', 'grpc_tools.protoc',
            '-I.', '--python_out=.', '--grpc_python_out=.',
            'clock.proto'
        ])
        print("gRPC code generation successful.")
        return True
    except Exception as e:
        print(f"Error generating gRPC code: {e}")
        return False

if __name__ == "__main__":
    # Generate the gRPC code before running experiments
    if generate_proto_code():
        run_experiments()
    else:
        print("Failed to generate gRPC code. Make sure grpcio-tools is installed.")
        print("Try: pip install grpcio-tools")