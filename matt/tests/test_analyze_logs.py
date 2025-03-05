import unittest
import tempfile
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analyze_logs import get_tick_rate, process_log_file, compute_jumps

class TestAnalyzeLogs(unittest.TestCase):

    def setUp(self):
        # Create a temporary log file with sample content.
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, "machine1_log.txt")
        with open(self.log_file, 'w') as f:
            f.write("2025-03-05 02:23:14,122 INFO: Machine machine1 initialized with tick rate 50 ticks per second\n")
            f.write("2025-03-05 02:23:14,123 INFO: Internal event: updated logical clock to 1, system_time=1741159394\n")
            f.write("2025-03-05 02:23:14,225 INFO: Internal event: updated logical clock to 2, system_time=1741159395\n")
            f.write("2025-03-05 02:23:14,325 INFO: Internal event: updated logical clock to 3, system_time=1741159396, queue_length=1\n")
            f.write("2025-03-05 02:23:14,425 INFO: Internal event: updated logical clock to 4, system_time=1741159397, queue_length=0\n")
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_get_tick_rate(self):
        tick_rate = get_tick_rate(self.log_file)
        self.assertEqual(tick_rate, 50)
    
    def test_process_log_file(self):
        events = process_log_file(self.log_file)
        # We expect 4 events.
        self.assertEqual(len(events), 4)
        # Check first event: (logical_clock, system_time, queue_length)
        self.assertEqual(events[0], (1, 1741159394, None))
        # Check third event has queue_length 1.
        self.assertEqual(events[2], (3, 1741159396, 1))
    
    def test_compute_jumps(self):
        events = process_log_file(self.log_file)
        jumps = compute_jumps(events)
        # Expected jumps: 2-1 = 1, 3-2 = 1, 4-3 = 1.
        self.assertEqual(jumps, [1, 1, 1])

if __name__ == '__main__':
    unittest.main()