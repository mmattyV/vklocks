import subprocess
import sys

def main():
    # Define configurations for three machines:
    # Each tuple: (machine_id, port, comma-separated peer addresses)
    configs = [
        ('machine1', '50051', 'localhost:50052,localhost:50053'),
        ('machine2', '50052', 'localhost:50051,localhost:50053'),
        ('machine3', '50053', 'localhost:50051,localhost:50052'),
    ]

    processes = []

    # Start each virtual machine process.
    for machine_id, port, peers in configs:
        cmd = ['python', 'virtual_machine.py', machine_id, port, peers]
        print(f"Starting {machine_id} on port {port} with peers {peers}")
        proc = subprocess.Popen(cmd)
        processes.append(proc)

    # Wait for all processes to complete.
    try:
        for proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        print("Keyboard interrupt received. Terminating all VMs.")
        for proc in processes:
            proc.terminate()
        sys.exit(0)

if __name__ == '__main__':
    main()