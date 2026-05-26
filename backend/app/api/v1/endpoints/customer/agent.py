"""Agent execution endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.services.customer.agent_service import AgentService
from app.api.deps import get_current_user

router = APIRouter()


@router.post("/execute/{lead_id}")
async def execute_agent(
    lead_id: str,
    agent_type: str = "research",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute the sales agent for a specific lead."""
    if agent_type not in ("research", "outreach", "follow_up", "cold_outreach"):
        raise HTTPException(status_code=400, detail="Invalid agent type")

    service = AgentService(db, current_user)
    result = await service.execute_agent(lead_id, agent_type)
    if not result:
        raise HTTPException(status_code=404, detail="Lead not found")
    return result


@router.get("/executions")
async def get_executions(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get agent execution history."""
    service = AgentService(db, current_user)
    executions = await service.get_executions(skip=skip, limit=limit)
    return {"executions": executions, "total": len(executions)}


@router.get("/executions/{execution_id}")
async def get_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific execution."""
    service = AgentService(db, current_user)
    execution = await service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution
