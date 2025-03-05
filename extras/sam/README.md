# Distributed Logical Clock System

This project implements a model of a small asynchronous distributed system with logical clocks. It uses gRPC for communication between virtual machines running at different speeds.

## Overview

The system consists of multiple virtual machines, each running at a different clock rate. Each machine:
- Maintains a logical clock
- Has a message queue for incoming messages
- Communicates with other machines via gRPC
- Logs all events with timestamps

The machines follow these rules:
1. On each clock cycle, if there's a message in the queue, the machine:
   - Processes one message
   - Updates its logical clock
   - Logs the receive event

2. If there's no message, the machine generates a random number (1-10):
   - If the value is 1-3, it sends a message to one or more other machines
   - Otherwise, it processes an internal event

## Requirements

- Python 3.7+
- gRPC and Protocol Buffers
- matplotlib (for visualization)

Install dependencies:
```
pip install grpcio grpcio-tools matplotlib
```

## Running the System

1. Generate the gRPC code:
```
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. clock.proto
```

2. Run the experiments:
```
python system_setup.py
```

This will:
- Create three virtual machines with random clock rates
- Run the system for 1 minute per experiment
- Repeat for different configurations (clock rates, event probabilities)

3. Analyze the logs:
```
python log_analyzer.py
```

## Experiment Configurations

The system can be run with different configurations:

1. **Standard Configuration**: 
   - Clock rates: 1-6 ticks per second
   - Internal event probability: 0.7
   - Run 5 times for 1 minute each

2. **Smaller Variation in Clock Cycles**:
   - Clock rates: 3-4 ticks per second
   - Internal event probability: 0.7

3. **Smaller Probability of Internal Events**:
   - Clock rates: 1-6 ticks per second
   - Internal event probability: 0.4

4. **Combined Configuration**:
   - Clock rates: 3-4 ticks per second
   - Internal event probability: 0.4

## Architecture Details

### Virtual Machine Implementation

Each virtual machine:
- Runs at a configurable clock rate (1-6 ticks per second)
- Uses gRPC server to receive messages
- Has gRPC clients to connect to other machines
- Follows Lamport's logical clock rules
- Logs all events to a log file

### Logical Clock

The logical clock follows Lamport's rules:
1. Increment clock on any internal event
2. Send current clock value with any message
3. When receiving a message, set clock to max(local_clock, received_clock) + 1

### Communication

The gRPC service defines:
- `SendMessage`: Method for sending logical clock values
- `ClockMessage`: Message containing sender ID, logical clock, and timestamp
- `ClockResponse`: Simple acknowledgment of receipt

### Log Analyzer

The log analyzer processes the logs to extract:
- Clock jumps: How much the logical clock increments each time
- Clock drift: Differences between logical clocks across machines
- Queue lengths: How many messages were waiting in each machine's queue
- Event distribution: Ratio of internal vs. communication events
- Communication patterns: Which machines communicated with each other