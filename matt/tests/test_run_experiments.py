import unittest
import tempfile
import os
import shutil
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from run_experiments import collect_logs, VM_CONFIGS

class TestRunExperiments(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory and switch to it.
        self.original_dir = os.getcwd()
        self.test_dir = tempfile.TemporaryDirectory()
        os.chdir(self.test_dir.name)
    
    def tearDown(self):
        os.chdir(self.original_dir)
        self.test_dir.cleanup()
    
    def test_collect_logs_creates_directory(self):
        # Create dummy log files for each machine.
        for machine_id, _, _ in VM_CONFIGS:
            with open(f"{machine_id}_log.txt", "w") as f:
                f.write("Dummy log content")
        collect_logs(1)
        self.assertTrue(os.path.isdir("experiment_run_1"))
        for machine_id, _, _ in VM_CONFIGS:
            self.assertTrue(os.path.exists(os.path.join("experiment_run_1", f"{machine_id}_log.txt")))

if __name__ == "__main__":
    unittest.main()