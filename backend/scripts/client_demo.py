import requests
import argparse
import os
import time

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000/api")


def create_job(text, strategy="round_robin"):
    r = requests.post(
        f"{BACKEND_URL}/jobs", json={"text": text, "balancing_strategy": strategy}
    )
    if r.status_code == 200:
        job = r.json()
        print(f"✓ Trabajo creado: {job['job_id']}")
        print(f"  - Longitud del texto: {job['text_length']}")
        print(f"  - Shards: {job['num_shards']}")
        return job["job_id"]
    else:
        print("Error creando job:", r.text)
        return None


def wait_for_job(job_id, poll_interval=1):
    print(f"Esperando el trabajo {job_id}...")
    while True:
        r = requests.get(f"{BACKEND_URL}/jobs/{job_id}")
        if r.status_code != 200:
            print("Error obteniendo job", r.text)
            return None
        job = r.json()
        if job["status"] == "completada":
            print("✓ Trabajo completado")
            print("Top words:")
            for item in job.get("top_words", []):
                print(f"  {item['word']}: {item['count']}")
            return job
        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text")
    parser.add_argument("--file")
    args = parser.parse_args()
    if args.text:
        text = args.text
    elif args.file:
        with open(args.file, "r") as f:
            text = f.read()
    else:
        print("Proporciona --text o --file")
        return
    job_id = create_job(text)
    if job_id:
        wait_for_job(job_id)


if __name__ == "__main__":
    main()
