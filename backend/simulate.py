#!/usr/bin/env python3
import subprocess
import time
import requests
import csv
import argparse
import os
import signal

BACKEND_URL = os.environ.get('BACKEND_URL', 'https://visual-map-reduce.preview.emergentagent.com/api')

def start_engines(num_mappers, num_reducers):
    """Start engine processes"""
    processes = []
    
    # Start mappers
    for i in range(num_mappers):
        engine_id = f"mapper-{i}"
        proc = subprocess.Popen([
            'python3', 'engine.py',
            '--engine-id', engine_id,
            '--role', 'mapper',
            '--capacity', '5'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append(proc)
        print(f"Started {engine_id}")
    
    # Start reducers
    for i in range(num_reducers):
        engine_id = f"reducer-{i}"
        proc = subprocess.Popen([
            'python3', 'engine.py',
            '--engine-id', engine_id,
            '--role', 'reducer',
            '--capacity', '5'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        processes.append(proc)
        print(f"Started {engine_id}")
    
    time.sleep(3)  # Wait for engines to register
    return processes

def stop_engines(processes):
    """Stop all engine processes"""
    for proc in processes:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    print("All engines stopped")

def run_job(text):
    """Run a job and return duration"""
    # Create job
    response = requests.post(f"{BACKEND_URL}/jobs", json={'text': text})
    if response.status_code != 200:
        return None
    
    job = response.json()
    job_id = job['job_id']
    
    # Poll until complete
    start_time = time.time()
    while True:
        response = requests.get(f"{BACKEND_URL}/jobs/{job_id}")
        if response.status_code != 200:
            return None
        
        job = response.json()
        if job['status'] == 'done':
            return job['duration_seconds']
        
        time.sleep(0.5)
        
        # Timeout after 60 seconds
        if time.time() - start_time > 60:
            return None

def run_simulation(text, engine_configs, output_file):
    """Run simulation with different engine configurations"""
    results = []
    
    print("\n" + "=" * 60)
    print("MapReduce Performance Simulation")
    print("=" * 60)
    
    for num_mappers, num_reducers in engine_configs:
        print(f"\nTesting with {num_mappers} mappers, {num_reducers} reducers...")
        
        # Start engines
        processes = start_engines(num_mappers, num_reducers)
        
        # Run job
        duration = run_job(text)
        
        if duration:
            print(f"  Duration: {duration:.2f} seconds")
            results.append({
                'mappers': num_mappers,
                'reducers': num_reducers,
                'duration': duration
            })
        else:
            print(f"  Failed or timed out")
        
        # Stop engines
        stop_engines(processes)
        time.sleep(2)  # Cool down
    
    # Write results to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['mappers', 'reducers', 'duration'])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n✓ Results saved to {output_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for result in results:
        print(f"  {result['mappers']}M + {result['reducers']}R: {result['duration']:.2f}s")

def main():
    parser = argparse.ArgumentParser(description='MapReduce Performance Simulation')
    parser.add_argument('--text-file', required=True, help='Input text file')
    parser.add_argument('--output', default='simulation_results.csv', help='Output CSV file')
    parser.add_argument('--configs', default='1,1;2,2;4,4', help='Engine configs (mappers,reducers;...)')
    
    args = parser.parse_args()
    
    # Read input text
    with open(args.text_file, 'r') as f:
        text = f.read()
    
    print(f"Text length: {len(text)} characters")
    
    # Parse configs
    configs = []
    for config in args.configs.split(';'):
        mappers, reducers = map(int, config.split(','))
        configs.append((mappers, reducers))
    
    # Run simulation
    run_simulation(text, configs, args.output)

if __name__ == '__main__':
    main()
