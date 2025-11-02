#!/usr/bin/env python3
import requests
import time
import argparse
import sys
import os

BACKEND_URL = os.environ.get('BACKEND_URL', 'https://visual-map-reduce.preview.emergentagent.com/api')

def create_job(text, strategy='round_robin'):
    """Create a new MapReduce job"""
    response = requests.post(f"{BACKEND_URL}/jobs", json={
        'text': text,
        'balancing_strategy': strategy
    })
    
    if response.status_code == 200:
        job = response.json()
        print(f"✓ Trabajo creado: {job['job_id']}")
        print(f"  - Longitud del texto: {job['text_length']} caracteres")
        print(f"  - Shards: {job['num_shards']}")
        return job['job_id']
    else:
        print(f"✗ Error creando trabajo: {response.text}")
        return None

def wait_for_job(job_id, poll_interval=1):
    """Poll job status until completion"""
    print(f"\nEsperando el trabajo {job_id}...")
    
    while True:
        response = requests.get(f"{BACKEND_URL}/jobs/{job_id}")
        
        if response.status_code == 200:
            job = response.json()
            status = job['status']
            
            print(f"  Estado: {status.upper()}", end='\r')
            
            if status == 'done':
                print("\n✓ ¡Trabajo completado!")
                print(f"  Duración: {job['duration_seconds']:.2f} segundos")
                print(f"\n  10 palabras más frecuentes:")
                for item in job['top_words']:
                    print(f"    {item['word']}: {item['count']}")
                return job
            
            time.sleep(poll_interval)
        else:
            print(f"\n✗ Error al obtener los trabajo: {response.text}")
            return None

def list_engines():
    """List all registered engines"""
    response = requests.get(f"{BACKEND_URL}/engines")
    
    if response.status_code == 200:
        engines = response.json()
        print(f"\nEngines registrados: {len(engines)}")
        for engine in engines:
            print(f"  - {engine['engine_id']} ({engine['role']}): {engine['current_load']}/{engine['capacity']} - {engine['status']}")
    else:
        print(f"✗ Error al obtener los engines: {response.text}")

def main():
    parser = argparse.ArgumentParser(description='MapReduce Client Demo')
    parser.add_argument('--text', help='Text to process')
    parser.add_argument('--file', help='File to process')
    parser.add_argument('--strategy', default='round_robin', choices=['round_robin', 'least_loaded'], help='Balancing strategy')
    parser.add_argument('--list-engines', action='store_true', help='List engines only')
    
    args = parser.parse_args()
    
    if args.list_engines:
        list_engines()
        return
    
    text = None
    
    if args.text:
        text = args.text
    elif args.file:
        with open(args.file, 'r') as f:
            text = f.read()
    else:
        print("Por favor, proporciona --text o --file")
        sys.exit(1)
    
    print("=" * 60)
    print("Demostración del cliente MapReduce")
    print("=" * 60)
    
    # Create job
    job_id = create_job(text, args.strategy)
    if not job_id:
        sys.exit(1)
    
    # Wait for completion
    result = wait_for_job(job_id)
    
    if result:
        print("\n" + "=" * 60)
        print("¡Trabajo completado exitosamente!")
        print("=" * 60)

if __name__ == '__main__':
    main()
