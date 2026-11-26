import uuid

import pipeline

MAX_JOBS = 50

jobs = {}


def create_job():
    job_id = uuid.uuid4().hex
    job = {"status": "running", "log": [], "report": None, "error": None}

    jobs[job_id] = job
    while len(jobs) > MAX_JOBS:
        jobs.pop(next(iter(jobs)))

    return job_id, job


def run_job(job, url):
    try:
        job["report"] = pipeline.scan_repo(url, job["log"])
        job["status"] = "done"
    except ValueError as error:
        job["error"] = str(error)
        job["status"] = "error"
    except Exception as error:
        job["error"] = f"Scan failed: {error}"
        job["status"] = "error"
