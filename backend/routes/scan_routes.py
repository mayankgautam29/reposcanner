from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

import jobs
from agents import fetcher_agent, report_agent

router = APIRouter()


class ScanRequest(BaseModel):
    url: str


@router.post("/scan")
def start_scan(request: ScanRequest, background_tasks: BackgroundTasks):
    try:
        fetcher_agent.parse_github_url(request.url)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    job_id, job = jobs.create_job()
    background_tasks.add_task(jobs.run_job, job, request.url)
    return {"id": job_id}


@router.get("/scan/{job_id}")
def get_scan(job_id: str):
    job = jobs.jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Scan not found. The server may have restarted, please scan again.")
    return job


@router.post("/report/pdf")
def download_pdf(report: dict):
    pdf = report_agent.build_pdf(report)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="scan_report.pdf"'},
    )
