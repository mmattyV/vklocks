import grpc
import time
import random
import queue
import logging
import threading
import datetime
import concurrent.futures
from datetime import datetime

# Import the generated gRPC code
import clock_pb2
import clock_pb2_grpc

class ClockServicer(clock_pb2_grpc.ClockServiceServicer):
    """Implements the ClockService service."""
    
    def __init__(self, vm):
        self.vm = vm
    
    def SendMessage(self, request, context):
        """Receive a message from another machine."""
        # Extract message details
        sender_id = request.sender_id
        logical_clock = request.logical_clock
        
        # Add to message queue
        self.vm.message_queue.put((sender_id, logical_clock))
        
        # Return acknowledgment
        return clock_pb2.ClockResponse(received=True)

class VirtualMachine:
    def __init__(self, machine_id, clock_rate, port, other_machines=None, internal_prob=0.7):
        """
        Initialize a virtual machine with specified parameters.
        
        Args:
            machine_id (int): Unique identifier for this machine
            clock_rate (int): Number of clock ticks per second (1-6)
            port (int): Port to listen on for incoming connections
            other_machines (list): List of (host, port) tuples for other machines
            internal_prob (float): Probability of internal events (0.0-1.0)
        """
        self.machine_id = machine_id
        self.clock_rate = clock_rate  # Ticks per second
        self.port = port
        self.host = 'localhost'
        self.other_machines = other_machines if other_machines else []
        self.internal_prob = internal_prob
        
        # Calculate action thresholds based on internal_prob
        # For internal_prob=0.7, actions 4-10 should have 0.7 probability (internal events)
        # and values 1-3 should have 0.3 probability (send events)
        self.action_threshold = int(10 - (self.internal_prob * 7))
        
        # Initialize logical clock
        self.logical_clock = 0
        
        # Initialize message queue
        self.message_queue = queue.Queue()
        
        # Create gRPC server
        self.server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=10))
        self.servicer = ClockServicer(self)
        clock_pb2_grpc.add_ClockServiceServicer_to_server(self.servicer, self.server)
        self.server.add_insecure_port(f"{self.host}:{self.port}")
        
        # Initialize clients for other machines
        self.stubs = {}  # Will hold gRPC stubs for other machines
        
        # Set up logging
        log_filename = f"machine_{machine_id}.log"
        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S.%f'
        )
        self.logger = logging.getLogger(f"Machine_{machine_id}")
        
        # Flag to control the machine's operation
        self.running = False
    
    def connect_to_other_machines(self):
        """Establish connections to other virtual machines."""
        for host, port in self.other_machines:
            channel = grpc.insecure_channel(f"{host}:{port}")
            stub = clock_pb2_grpc.ClockServiceStub(channel)
            self.stubs[(host, port)] = stub
            print(f"Machine {self.machine_id} connected to {host}:{port}")
    
    def send_message(self, target_machine):
        """
        Send a message containing the local logical clock time to a target machine.
        
        Args:
            target_machine (tuple): (host, port) of the target machine
        """
        try:
            # Update logical clock for send event
            self.logical_clock += 1
            
            # Create timestamp for logging
            system_time = datetime.now()
            timestamp_str = system_time.strftime("%Y-%m-%d %H:%M:%S.%f")
            
            # Create and send message
            message = clock_pb2.ClockMessage(
                sender_id=self.machine_id,
                logical_clock=self.logical_clock,
                timestamp=timestamp_str
            )
            
            # Send the message using gRPC stub
            response = self.stubs[target_machine].SendMessage(message)
            
            # Log the send event
            self.logger.info(
                f"SEND - System Time: {system_time}, " +
                f"Logical Clock: {self.logical_clock}, " +
                f"Destination: Machine at {target_machine}"
            )
        except Exception as e:
            print(f"Error sending message to {target_machine}: {e}")
    
    def process_cycle(self):
        """Process one clock cycle according to the rules."""
        # Check if there's a message in the queue
        if not self.message_queue.empty():
            # Process one message
            sender_id, received_clock = self.message_queue.get()
            
            # Update logical clock according to Lamport's rule
            self.logical_clock = max(self.logical_clock, received_clock) + 1
            
            # Log the receive event
            system_time = datetime.now()
            queue_length = self.message_queue.qsize()
            self.logger.info(
                f"RECEIVE - System Time: {system_time}, " +
                f"Queue Length: {queue_length}, " +
                f"Logical Clock: {self.logical_clock}, " +
                f"From: Machine {sender_id}"
            )
        else:
            # No message, generate random action (adjusted for internal_prob)
            action = random.randint(1, 10)
            
            # Remap actions based on internal_prob
            # Lower action_threshold means more communication events
            if action <= self.action_threshold and len(self.other_machines) > 0:
                # Determine the type of communication event based on the action
                comm_type = action % 3 + 1  # Distributes actions 1-3
                
                if comm_type == 1:
                    # Send to one random machine
                    target = random.choice(self.other_machines)
                    self.send_message(target)
                    
                elif comm_type == 2 and len(self.other_machines) > 0:
                    # Send to another random machine (different from the first if possible)
                    if len(self.other_machines) > 1:
                        # Choose a different machine
                        target = random.choice([m for m in self.other_machines if m != self.other_machines[0]])
                    else:
                        target = self.other_machines[0]
                    self.send_message(target)
                    
                elif comm_type == 3:
                    # Send to all other machines
                    for machine in self.other_machines:
                        self.send_message(machine)
            else:
                # Internal event
                self.logical_clock += 1
                
                # Log the internal event
                system_time = datetime.now()
                self.logger.info(
                    f"INTERNAL - System Time: {system_time}, " +
                    f"Logical Clock: {self.logical_clock}"
                )
    
    def run(self, duration_seconds=60):
        """
        Run the virtual machine for the specified duration.
        
        Args:
            duration_seconds (int): How long to run the machine, in seconds
        """
        self.running = True
        
        # Start the gRPC server
        self.server.start()
        print(f"Machine {self.machine_id} server started on port {self.port}")
        
        # Allow time for all machines to start up
        time.sleep(2)
        
        # Connect to other machines
        self.connect_to_other_machines()
        
        # Calculate sleep time based on clock rate
        sleep_time = 1.0 / self.clock_rate
        
        # Run for the specified duration
        start_time = time.time()
        try:
            while time.time() - start_time < duration_seconds:
                self.process_cycle()
                time.sleep(sleep_time)
        except KeyboardInterrupt:
            print(f"Machine {self.machine_id} stopped by user.")
        finally:
            self.running = False
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources when shutting down."""
        # Shut down the gRPC server
        self.server.stop(0)
        print(f"Machine {self.machine_id} shut down.")