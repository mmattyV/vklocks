import sys
import os

# Add the parent directory to sys.path so we can import our modules.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Override sys.argv with dummy values to satisfy the argument parser in virtual_machine.py.
sys.argv = ["dummy.py", "dummy", "50051", "localhost:50052,localhost:50053"]

import unittest
import tempfile
import time
import queue
from unittest.mock import patch

from virtual_machine import VirtualMachine, TIGHT_MODE

# Dummy message to simulate a gRPC message.
class DummyMessage:
    def __init__(self, machine_id, logical_clock, system_time):
        self.machine_id = machine_id
        self.logical_clock = logical_clock
        self.system_time = system_time

# Dummy logger to capture log messages.
class DummyLogger:
    def __init__(self):
        self.messages = []
    def info(self, msg):
        self.messages.append(msg)
    def error(self, msg):
        self.messages.append(msg)

# Generator function to simulate time.time() incrementing.
def time_generator(start=100.0, increment=0.5):
    t = start
    while True:
        yield t
        t += increment

class TestVirtualMachine(unittest.TestCase):
    def setUp(self):
        # Create a VirtualMachine instance with dummy configuration.
        self.dummy_logger = DummyLogger()
        self.vm = VirtualMachine("test_vm", 50051, ["localhost:50052"])
        # Replace the real logger with our dummy logger.
        self.vm.logger = self.dummy_logger
        # Force a specific tick rate for consistency.
        self.vm.tick_rate = 2

    @patch("time.sleep", return_value=None)
    def test_internal_event_processing(self, patched_sleep):
        # Test that an internal event increments the logical clock.
        initial_clock = self.vm.logical_clock
        self.vm.run(duration=1)
        self.assertGreater(self.vm.logical_clock, initial_clock)

    @patch("time.sleep", return_value=None)
    def test_message_processing(self, patched_sleep):
        # Replace time.time with our generator to simulate controlled time increments.
        gen = time_generator(start=100.0, increment=0.5)
        with patch("time.time", side_effect=lambda: next(gen)):
            # Test that a message in the queue is processed correctly.
            dummy_msg = DummyMessage("other_vm", 10, 100)  # Dummy system_time of 100.
            self.vm.message_queue.put(dummy_msg)
            self.vm.logical_clock = 5  # Set lower than dummy message's clock.
            self.vm.run(duration=1)
            # Expect the new clock to be max(5, 10) + 1 = 11.
            self.assertEqual(self.vm.logical_clock, 11)

    @patch("time.sleep", return_value=None)
    def test_tight_mode_send_probability(self, patched_sleep):
        # Force tight mode for this test.
        global TIGHT_MODE
        original_tight = TIGHT_MODE
        TIGHT_MODE = True
        
        self.vm.message_queue = queue.Queue()
        self.vm.logical_clock = 0
        
        # Run the simulation briefly.
        self.vm.run(duration=2)
        # Check that at least one log entry indicates a send event.
        send_events = [msg for msg in self.dummy_logger.messages 
                       if "Sent event" in msg or "Broadcast sent" in msg]
        self.assertTrue(len(send_events) > 0)
        
        TIGHT_MODE = original_tight

if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]])