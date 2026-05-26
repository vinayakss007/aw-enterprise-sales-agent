
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.services.customer.agent_service import AgentService
from app.services.quota_service import QuotaService

router = APIRouter()

@router.post("/execute/{lead_id}")
async def execute_agent(
    lead_id: str,
    agent_type: str = "research",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute the sales agent for a specific lead
    """
    QuotaService(db, current_user).check_agent_run()
    agent_service = AgentService(db, current_user)
    result = await agent_service.execute_agent(lead_id, agent_type)
    
    if not result:
        raise HTTPException(status_code=500, detail="Agent execution failed")
    
    return result

@router.get("/executions")
async def get_agent_executions(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get agent execution history for the current user
    """
    agent_service = AgentService(db, current_user)
    executions = await agent_service.get_executions(skip=skip, limit=limit)
    return {"executions": executions, "total": len(executions)}

@router.get("/executions/{execution_id}")
async def get_agent_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific agent execution by ID
    """
    agent_service = AgentService(db, current_user)
    execution = await agent_service.get_execution(execution_id)
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return execution