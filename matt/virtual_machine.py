import grpc
from concurrent import futures
import time
import threading
import queue
import random
import sys
import logging

# Import the generated gRPC classes (from machine.proto)
import machine_pb2
import machine_pb2_grpc

class MachineServiceServicer(machine_pb2_grpc.MachineServiceServicer):
    """
    gRPC Service Implementation for processing clock messages.
    
    This class implements the SendClockMessage RPC defined in machine.proto.
    It logs incoming messages and enqueues them for further processing.
    """
    def __init__(self, message_queue, logger):
        """
        Initializes the service servicer with a message queue and a logger.
        
        Parameters:
            message_queue (queue.Queue): A thread-safe queue for storing incoming messages.
            logger (logging.Logger): A logger instance for recording events.
        """
        self.message_queue = message_queue
        self.logger = logger

    def SendClockMessage(self, request, context):
        """
        Handles the SendClockMessage RPC call.
        
        Logs the receipt of a message, enqueues it for processing, and returns an acknowledgement.
        
        Parameters:
            request (machine_pb2.ClockMessage): The incoming clock message.
            context (grpc.ServicerContext): The context for the RPC call.
            
        Returns:
            machine_pb2.Ack: An acknowledgement message indicating success.
        """
        log_entry = (f"Received message from {request.machine_id}: "
                     f"received_clock={request.logical_clock}, "
                     f"system_time={request.system_time}")
        self.logger.info(log_entry)
        self.message_queue.put(request)
        return machine_pb2.Ack(success=True)

class VirtualMachine:
    """
    Represents a virtual machine in a simulated asynchronous distributed system.
    
    This class manages a logical clock, a message queue, and a gRPC server
    for inter-machine communication. It processes events based on a tick rate,
    which is randomly chosen during initialization.
    """
    def __init__(self, machine_id, port, peer_addresses):
        """
        Initializes the virtual machine with its identifier, network port, and peer addresses.
        
        Sets up the message queue, logical clock, tick rate, and logging mechanisms.
        
        Parameters:
            machine_id (str): Unique identifier for the virtual machine.
            port (int): Port number on which the gRPC server will listen.
            peer_addresses (list): List of peer addresses (e.g., ["localhost:50052", "localhost:50053"]).
        """
        self.machine_id = machine_id
        self.port = port
        self.peer_addresses = peer_addresses  # e.g. ["localhost:50052", "localhost:50053"]
        self.message_queue = queue.Queue()      # Unconstrained network queue.
        self.logical_clock = 0
        self.tick_rate = random.randint(1, 6)     # Clock ticks per real second.
        self.server = None

        # Set up logging to a file named after the machine.
        self.logger = logging.getLogger(self.machine_id)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
        file_handler = logging.FileHandler(f'{self.machine_id}_log.txt')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        # Also log to console.
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # Log the clock speed (tick rate) at initialization.
        self.logger.info(f"Machine {self.machine_id} initialized with tick rate {self.tick_rate} ticks per second")

    def start_server(self):
        """
        Starts the gRPC server to listen for incoming clock messages.
        
        Creates a gRPC server with a thread pool executor, registers the
        MachineServiceServicer, binds the server to the specified port, and starts it.
        """
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        machine_pb2_grpc.add_MachineServiceServicer_to_server(
            MachineServiceServicer(self.message_queue, self.logger), self.server)
        self.server.add_insecure_port(f'[::]:{self.port}')
        self.server.start()
        self.logger.info(f"gRPC server started on port {self.port}")

    def send_message(self, target, logical_clock):
        """
        Sends a clock message to a target machine using gRPC.
        
        Establishes a gRPC channel to the target, sends a ClockMessage containing
        the machine's identifier, logical clock, and system time, and logs the event.
        
        Parameters:
            target (str): The target machine's address (e.g., "localhost:50052").
            logical_clock (int): The current logical clock value to be sent.
        """
        channel = grpc.insecure_channel(target)
        stub = machine_pb2_grpc.MachineServiceStub(channel)
        system_time = int(time.time())
        message = machine_pb2.ClockMessage(
            machine_id=self.machine_id,
            logical_clock=logical_clock,
            system_time=system_time
        )
        try:
            response = stub.SendClockMessage(message)
            if response.success:
                log_entry = (f"Sent message to {target}: "
                             f"sent_clock={logical_clock}, system_time={system_time}")
                self.logger.info(log_entry)
        except grpc.RpcError as e:
            self.logger.error(f"Error sending message to {target}: {e}")

    def log_internal_event(self):
        """
        Logs an internal event where the machine updates its logical clock
        without sending or receiving a message.
        
        The log entry includes the updated logical clock and the current system time.
        """
        system_time = int(time.time())
        log_entry = (f"Internal event: updated logical clock to {self.logical_clock}, "
                     f"system_time={system_time}")
        self.logger.info(log_entry)

    def log_receive_event(self, queue_length):
        """
        Logs an event for processing a received message.
        
        The log entry includes the updated logical clock, the system time,
        and the current message queue length.
        
        Parameters:
            queue_length (int): The current number of messages in the queue.
        """
        system_time = int(time.time())
        log_entry = (f"Processed received message: updated logical clock to {self.logical_clock}, "
                     f"system_time={system_time}, queue_length={queue_length}")
        self.logger.info(log_entry)

    def run(self, duration=60):
        """
        Runs the main simulation loop for a specified duration.
        
        On each tick:
          - If there is a message in the queue, processes it and updates the logical clock.
          - If no message is available, randomly selects an event: send message(s) or internal event.
          - Enforces a fixed tick rate as defined by the machine's tick_rate.
        
        Parameters:
            duration (int): Duration in seconds for which the simulation will run.
        """
        start_time = time.time()
        while time.time() - start_time < duration:
            tick_start = time.time()
            if not self.message_queue.empty():
                # Process one message from the queue.
                message = self.message_queue.get()
                # Update logical clock: max(local_clock, received_clock) + 1.
                self.logical_clock = max(self.logical_clock, message.logical_clock) + 1
                self.log_receive_event(self.message_queue.qsize())
            else:
                # No message available; decide which event to execute.
                event = random.randint(1, 10)
                if event in (1, 2, 3):
                    # Sending event: update clock and send message(s).
                    self.logical_clock += 1
                    system_time = int(time.time())
                    if event == 3:
                        # Broadcast to all peers.
                        for peer in self.peer_addresses:
                            self.send_message(peer, self.logical_clock)
                        self.logger.info(f"Broadcast sent: updated logical clock to {self.logical_clock}, system_time={system_time}")
                    else:
                        # Send to one randomly selected peer.
                        peer = random.choice(self.peer_addresses)
                        self.send_message(peer, self.logical_clock)
                        self.logger.info(f"Sent event to {peer}: updated logical clock to {self.logical_clock}, system_time={system_time}")
                else:
                    # Internal event: update the clock.
                    self.logical_clock += 1
                    self.log_internal_event()

            # Enforce the tick rate (only a fixed number of operations per second).
            time_to_next_tick = max(0, (1 / self.tick_rate) - (time.time() - tick_start))
            time.sleep(time_to_next_tick)

    def stop_server(self):
        """
        Stops the gRPC server if it is running.
        
        This method shuts down the server and logs the shutdown event.
        """
        if self.server:
            self.server.stop(0)
            self.logger.info("gRPC server stopped")

if __name__ == '__main__':
    """
    Entry point for the virtual machine simulation.
    
    Expects the following command-line arguments:
        1. machine_id: Unique identifier for the virtual machine.
        2. port: The port on which the gRPC server will listen.
        3. peer_addresses: Comma-separated list of peer addresses.
    
    Example usage:
        python virtual_machine.py machine1 50051 localhost:50052,localhost:50053
    """
    if len(sys.argv) != 4:
        print("Usage: python virtual_machine.py <machine_id> <port> <peer_addresses>")
        print("Example: python virtual_machine.py machine1 50051 localhost:50052,localhost:50053")
        sys.exit(1)

    machine_id = sys.argv[1]
    port = int(sys.argv[2])
    peer_addresses = sys.argv[3].split(',')

    vm = VirtualMachine(machine_id, port, peer_addresses)

    # Start the gRPC server in a separate thread.
    server_thread = threading.Thread(target=vm.start_server)
    server_thread.daemon = True
    server_thread.start()

    try:
        # Run the simulation for 60 seconds.
        vm.run(duration=60)
    except KeyboardInterrupt:
        pass
    finally:
        vm.stop_server()
        print("Server stopped")