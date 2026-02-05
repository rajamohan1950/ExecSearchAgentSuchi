"""Proxy router: forwards outreach-related requests to the outreach-agent service."""

import logging

import httpx
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/outreach", tags=["outreach"])

TIMEOUT = httpx.Timeout(30.0, connect=5.0)


async def _proxy_get(path: str, params: dict = None) -> JSONResponse:
    """Forward GET request to outreach-agent service."""
    url = f"{settings.outreach_agent_url}/api/v1{path}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, params=params)
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Outreach agent service unavailable")
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")


async def _proxy_post(path: str, json_body: dict = None) -> JSONResponse:
    """Forward POST request to outreach-agent service."""
    url = f"{settings.outreach_agent_url}/api/v1{path}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(url, json=json_body)
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Outreach agent service unavailable")
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")


# ── Firms ─────────────────────────────────────────────────

@router.post("/firms/bulk-upload")
async def proxy_bulk_upload(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    """Proxy bulk upload to outreach agent."""
    url = f"{settings.outreach_agent_url}/api/v1/firms/bulk-upload"
    try:
        content = await file.read()
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                url,
                files={"file": (file.filename, content, file.content_type)},
            )
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Outreach agent service unavailable")
    except Exception as e:
        logger.error(f"Proxy upload error: {e}")
        raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")


@router.get("/firms")
async def proxy_list_firms(request: Request, user=Depends(get_current_user)):
    return await _proxy_get("/firms", params=dict(request.query_params))


@router.get("/firms/{firm_id}")
async def proxy_get_firm(firm_id: str, user=Depends(get_current_user)):
    return await _proxy_get(f"/firms/{firm_id}")


@router.post("/firms")
async def proxy_create_firm(request: Request, user=Depends(get_current_user)):
    body = await request.json()
    return await _proxy_post("/firms", json_body=body)


@router.patch("/firms/{firm_id}")
async def proxy_update_firm(firm_id: str, request: Request, user=Depends(get_current_user)):
    url = f"{settings.outreach_agent_url}/api/v1/firms/{firm_id}"
    body = await request.json()
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.patch(url, json=body)
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Outreach agent service unavailable")


@router.delete("/firms/{firm_id}")
async def proxy_delete_firm(firm_id: str, user=Depends(get_current_user)):
    url = f"{settings.outreach_agent_url}/api/v1/firms/{firm_id}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.delete(url)
            return JSONResponse(content=None if resp.status_code == 204 else resp.json(), status_code=resp.status_code)
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Outreach agent service unavailable")


# ── Outreach ──────────────────────────────────────────────

@router.get("/threads")
async def proxy_list_threads(request: Request, user=Depends(get_current_user)):
    return await _proxy_get("/outreach/threads", params=dict(request.query_params))


@router.get("/threads/{thread_id}")
async def proxy_get_thread(thread_id: str, user=Depends(get_current_user)):
    return await _proxy_get(f"/outreach/threads/{thread_id}")


@router.post("/trigger/{contact_id}")
async def proxy_trigger_outreach(contact_id: str, user=Depends(get_current_user)):
    return await _proxy_post(f"/outreach/trigger/{contact_id}")


@router.get("/agent-status")
async def proxy_agent_status(user=Depends(get_current_user)):
    return await _proxy_get("/outreach/agent-status")


# ── Metrics ───────────────────────────────────────────────

@router.get("/metrics/summary")
async def proxy_metrics_summary(user=Depends(get_current_user)):
    return await _proxy_get("/metrics/summary")


@router.get("/metrics/actions")
async def proxy_metrics_actions(request: Request, user=Depends(get_current_user)):
    return await _proxy_get("/metrics/actions", params=dict(request.query_params))


@router.get("/metrics/briefings")
async def proxy_metrics_briefings(request: Request, user=Depends(get_current_user)):
    return await _proxy_get("/metrics/briefings", params=dict(request.query_params))
