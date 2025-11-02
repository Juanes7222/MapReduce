import argparse
import subprocess
import time
import csv
import requests
import os

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000/api")


def start_engine_proc(engine_id, role, capacity=5):
    return subprocess.Popen(
        [
            "python3",
            "scripts/engine.py",
            "--engine-id",
            engine_id,
            "--role",
            role,
            "--capacity",
            str(capacity),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def start_engines(num_mappers, num_reducers):
    procs = []
    for i in range(num_mappers):
        procs.append(start_engine_proc(f"mapper-{i}", "mapper"))
        print(f"mapper-{i} iniciado")
    for i in range(num_reducers):
        procs.append(start_engine_proc(f"reducer-{i}", "reducer"))
        print(f"reducer-{i} iniciado")
    time.sleep(3)
    return procs


def stop_engines(procs):
    for p in procs:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
    print("Engines detenidos")


def run_job(text, timeout=60):
    r = requests.post(f"{BACKEND_URL}/jobs", json={"text": text})
    if r.status_code != 200:
        return None
    job = r.json()
    start = time.time()
    while True:
        r = requests.get(f"{BACKEND_URL}/jobs/{job['job_id']}")
        if r.status_code != 200:
            return None
        j = r.json()
        if j["status"] == "completada":
            return j["duration_seconds"]
        if time.time() - start > timeout:
            return None
        time.sleep(0.5)


def run_simulation(text, configs, output_file):
    results = []
    for m, r in configs:
        print(f"Probando {m} mappers, {r} reducers")
        procs = start_engines(m, r)
        duration = run_job(text)
        if duration:
            print(f"Duración: {duration:.2f}s")
            results.append({"mappers": m, "reducers": r, "duration": duration})
        else:
            print("Error o timeout")
        stop_engines(procs)
        time.sleep(2)
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["mappers", "reducers", "duration"])
        writer.writeheader()
        writer.writerows(results)
    print("Resultados guardados en", output_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-file", required=True)
    parser.add_argument("--configs", default="1,1;2,2;4,4")
    parser.add_argument("--output", default="simulation_results.csv")
    args = parser.parse_args()
    with open(args.text_file, "r") as f:
        text = f.read()
    configs = []
    for c in args.configs.split(";"):
        m, r = map(int, c.split(","))
        configs.append((m, r))
    run_simulation(text, configs, args.output)


if __name__ == "__main__":
    main()
