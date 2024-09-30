import subprocess
import sys
import os
import argparse
import yaml

def load_config(config_path):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def run_slave(slave_config):
    try:
        cmd = [
            sys.executable,
            slave_config['script_path'],
            slave_config['direction'],
            slave_config['video_path'],
            '--host', slave_config['host'],
            '--port', str(slave_config['port'])
        ]
        process = subprocess.Popen(cmd, 
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)
        print(f"Started {slave_config['direction']} slave process with PID: {process.pid}")
        return process
    except Exception as e:
        print(f"Error starting {slave_config['direction']} slave: {e}")
        return None

def main(config_path):
    config = load_config(config_path)
    processes = {}
    try:
        for slave_config in config['slaves']:
            processes[slave_config['direction']] = run_slave(slave_config)
        
        print("All slave processes started. Press Ctrl+C to stop all processes.")
        
        # Wait for processes to complete (or KeyboardInterrupt)
        for process in processes.values():
            if process:
                process.wait()
    
    except KeyboardInterrupt:
        print("\nStopping all slave processes...")
    finally:
        for direction, process in processes.items():
            if process:
                process.terminate()
                print(f"Terminated {direction} slave process")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch multiple slave programs for traffic monitoring")
    parser.add_argument("config", help="/home/adityaa/Desktop/Smart India Hackathon/master-slave copy/slaves.yaml")
    args = parser.parse_args()
    
    main(args.config)