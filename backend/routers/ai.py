"""AI-powered features API routes."""
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import AIAnalysisRequest, AIAnalysisResponse
from auth import get_current_user
from ai_categorization import ai_service

router = APIRouter(prefix="/api/ai", tags=["AI Features"])


@router.post("/analyze", response_model=AIAnalysisResponse)
async def analyze_ticket_content(
    request: AIAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze ticket content and provide AI-powered suggestions."""
    analysis = ai_service.analyze_ticket(
        title=request.title,
        description=request.description,
        db=db
    )

    return AIAnalysisResponse(**analysis)


@router.post("/suggest-category")
async def suggest_category(
    title: str = Body(...),
    description: str = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get category suggestion for ticket content."""
    category = ai_service.suggest_category(title, description, db)

    return {
        "suggested_category_id": category.id if category else None,
        "suggested_category_name": category.name if category else None
    }


@router.post("/suggest-priority")
async def suggest_priority(
    title: str = Body(...),
    description: str = Body(...),
    current_user: User = Depends(get_current_user)
):
    """Get priority suggestion for ticket content."""
    priority = ai_service.suggest_priority(title, description)

    return {
        "suggested_priority": priority.value
    }
