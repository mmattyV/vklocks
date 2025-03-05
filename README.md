# vklocks

## Overview

This repository simulates an asynchronous distributed system using multiple virtual machines (VMs) that communicate via gRPC. Each VM models a machine running at a specific tick rate with its own logical clock and message queue. The system is configurable so that you can experiment with different tick rate ranges and probabilities for internal events.

## Repository Structure

- **virtual_machine.py**: Main code for the virtual machine.
- **run_experiments.py**: Script to run multiple experiment runs, launch all VMs, and collect logs.
- **analyze_logs.py**: Script to analyze log files and compute statistics (such as clock jumps, drift, and message queue lengths).
- **machine.proto**: Protocol Buffers file defining the gRPC service and messages.
- **tests/**: Folder containing unit tests for various components of the system.

## Installation

1. Clone the repository:
   
   git clone https://github.com/mmattyV/vklocks.git

2. Change into the repository directory:
   
   cd vklocks

3. Activate the virtual environment:
 
   On Windows: venv\Scripts\activate  
   On macOS/Linux: source venv/bin/activate

4. Install dependencies:

   pip install -r requirements.txt

5. Generate gRPC stubs (if not already generated):

   python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. machine.proto

## Running the Program

You can run an individual virtual machine using the following command:

   python virtual_machine.py <machine_id> <port> <peer_addresses> [--tight] [--min-ticks MIN_TICKS] [--max-ticks MAX_TICKS]

For example, to run machine1 in tight mode with tick rates forced between 3 and 4 ticks per second:

   python virtual_machine.py machine1 50051 localhost:50052,localhost:50053 --tight --min-ticks 3 --max-ticks 4

## Running Experiments

The `run_experiments.py` script automates running a series of experiments. It launches all three VMs concurrently, runs each experiment for a set duration (default 60 seconds per run), and collects the log files into run-specific directories.

To run the experiments, execute:

   python run_experiments.py

This script will create directories named experiment_run_1, experiment_run_2, etc., containing the logs from each run.

## Running Tests

Unit tests are located in the `tests` folder. To run all tests, make sure your virtual environment is activated and run:

   python -m unittest discover

Alternatively, if you have pytest installed, you can run:

   pytest

## Additional Notes

- The tick rate range and event probability can be controlled via command-line arguments. The default configuration uses a tick rate range of 1–6 ticks per second. When running in tight mode (using the --tight flag), the probability of an internal event is reduced, leading to more send events.
- Experiment parameters (such as the number of runs and run duration) can be modified in `run_experiments.py`.
- Detailed log analysis is available in `analyze_logs.py` to help study logical clock jump sizes, drift, and message queue dynamics.

Enjoy experimenting with vklocks and exploring the dynamics of distributed system synchronization!