"""Analytics and reporting API routes."""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_

from database import get_db
from models import (
    User, Ticket, TicketComment, TicketStatus,
    TicketPriority, UserRole, Category
)
from auth import get_current_user, require_technician

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard")
async def get_dashboard_stats(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics."""
    # Date range
    start_date = datetime.utcnow() - timedelta(days=days)

    # Build base query based on user role
    base_query = db.query(Ticket)
    if current_user.role == UserRole.USER:
        base_query = base_query.filter(
            or_(
                Ticket.created_by == current_user.id,
                Ticket.assigned_to == current_user.id
            )
        )

    # Total tickets
    total_tickets = base_query.count()

    # Tickets by status
    tickets_by_status = dict(
        db.query(
            Ticket.status,
            func.count(Ticket.id)
        ).filter(
            Ticket.created_at >= start_date if current_user.role != UserRole.USER else and_(
                Ticket.created_at >= start_date,
                or_(
                    Ticket.created_by == current_user.id,
                    Ticket.assigned_to == current_user.id
                )
            )
        ).group_by(Ticket.status).all()
    )

    # Tickets by priority
    tickets_by_priority = dict(
        db.query(
            Ticket.priority,
            func.count(Ticket.id)
        ).filter(
            Ticket.created_at >= start_date if current_user.role != UserRole.USER else and_(
                Ticket.created_at >= start_date,
                or_(
                    Ticket.created_by == current_user.id,
                    Ticket.assigned_to == current_user.id
                )
            )
        ).group_by(Ticket.priority).all()
    )

    # Recently created tickets (last 7 days)
    recent_tickets = base_query.filter(
        Ticket.created_at >= datetime.utcnow() - timedelta(days=7)
    ).count()

    # Open tickets (new, assigned, in_progress)
    open_tickets = base_query.filter(
        Ticket.status.in_([TicketStatus.NEW, TicketStatus.ASSIGNED, TicketStatus.IN_PROGRESS])
    ).count()

    # Resolved tickets
    resolved_tickets = base_query.filter(
        Ticket.status == TicketStatus.RESOLVED
    ).count()

    # SLA breaches
    sla_breaches = base_query.filter(
        or_(
            Ticket.sla_response_breached == True,
            Ticket.sla_resolution_breached == True
        )
    ).count()

    return {
        "total_tickets": total_tickets,
        "recent_tickets": recent_tickets,
        "open_tickets": open_tickets,
        "resolved_tickets": resolved_tickets,
        "sla_breaches": sla_breaches,
        "tickets_by_status": {
            status.value: count for status, count in tickets_by_status.items()
        },
        "tickets_by_priority": {
            priority.value: count for priority, count in tickets_by_priority.items()
        }
    }


@router.get("/tickets/trend")
async def get_ticket_trend(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Get ticket creation trend over time."""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get tickets grouped by date
    results = db.query(
        func.date(Ticket.created_at).label('date'),
        func.count(Ticket.id).label('count')
    ).filter(
        Ticket.created_at >= start_date
    ).group_by(
        func.date(Ticket.created_at)
    ).order_by('date').all()

    return {
        "period_days": days,
        "data": [
            {
                "date": str(result.date),
                "count": result.count
            }
            for result in results
        ]
    }


@router.get("/tickets/by-category")
async def get_tickets_by_category(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Get ticket distribution by category."""
    start_date = datetime.utcnow() - timedelta(days=days)

    results = db.query(
        Category.name,
        func.count(Ticket.id).label('count')
    ).join(
        Ticket, Ticket.category_id == Category.id
    ).filter(
        Ticket.created_at >= start_date
    ).group_by(Category.name).all()

    # Include tickets without category
    uncategorized = db.query(Ticket).filter(
        Ticket.category_id == None,
        Ticket.created_at >= start_date
    ).count()

    data = [{"category": name, "count": count} for name, count in results]
    if uncategorized > 0:
        data.append({"category": "Uncategorized", "count": uncategorized})

    return {
        "period_days": days,
        "data": data
    }


@router.get("/performance")
async def get_performance_metrics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Get performance metrics."""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Average resolution time (in hours)
    resolved_tickets = db.query(Ticket).filter(
        Ticket.status == TicketStatus.RESOLVED,
        Ticket.resolved_at.isnot(None),
        Ticket.created_at >= start_date
    ).all()

    if resolved_tickets:
        total_hours = sum(
            (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
            for ticket in resolved_tickets
        )
        avg_resolution_time = total_hours / len(resolved_tickets)
    else:
        avg_resolution_time = 0

    # Average first response time (in hours)
    responded_tickets = db.query(Ticket).filter(
        Ticket.first_response_at.isnot(None),
        Ticket.created_at >= start_date
    ).all()

    if responded_tickets:
        total_hours = sum(
            (ticket.first_response_at - ticket.created_at).total_seconds() / 3600
            for ticket in responded_tickets
        )
        avg_response_time = total_hours / len(responded_tickets)
    else:
        avg_response_time = 0

    # SLA compliance rate
    total_with_sla = db.query(Ticket).filter(
        Ticket.sla_policy_id.isnot(None),
        Ticket.created_at >= start_date
    ).count()

    breached_sla = db.query(Ticket).filter(
        Ticket.sla_policy_id.isnot(None),
        Ticket.created_at >= start_date,
        or_(
            Ticket.sla_response_breached == True,
            Ticket.sla_resolution_breached == True
        )
    ).count()

    sla_compliance_rate = (
        ((total_with_sla - breached_sla) / total_with_sla * 100)
        if total_with_sla > 0 else 100.0
    )

    return {
        "period_days": days,
        "avg_resolution_time_hours": round(avg_resolution_time, 2),
        "avg_response_time_hours": round(avg_response_time, 2),
        "sla_compliance_rate": round(sla_compliance_rate, 2),
        "total_resolved": len(resolved_tickets),
        "total_sla_breaches": breached_sla
    }


@router.get("/technician-performance")
async def get_technician_performance(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Get performance metrics by technician."""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get all technicians
    technicians = db.query(User).filter(
        User.role.in_([UserRole.TECHNICIAN, UserRole.ADMIN])
    ).all()

    performance_data = []

    for tech in technicians:
        # Assigned tickets
        assigned_count = db.query(Ticket).filter(
            Ticket.assigned_to == tech.id,
            Ticket.created_at >= start_date
        ).count()

        # Resolved tickets
        resolved_count = db.query(Ticket).filter(
            Ticket.assigned_to == tech.id,
            Ticket.status == TicketStatus.RESOLVED,
            Ticket.created_at >= start_date
        ).count()

        # Average resolution time
        resolved_tickets = db.query(Ticket).filter(
            Ticket.assigned_to == tech.id,
            Ticket.status == TicketStatus.RESOLVED,
            Ticket.resolved_at.isnot(None),
            Ticket.created_at >= start_date
        ).all()

        if resolved_tickets:
            total_hours = sum(
                (ticket.resolved_at - ticket.created_at).total_seconds() / 3600
                for ticket in resolved_tickets
            )
            avg_resolution_time = total_hours / len(resolved_tickets)
        else:
            avg_resolution_time = 0

        performance_data.append({
            "technician_id": tech.id,
            "technician_name": f"{tech.first_name or ''} {tech.last_name or ''}".strip() or tech.username,
            "assigned_tickets": assigned_count,
            "resolved_tickets": resolved_count,
            "avg_resolution_time_hours": round(avg_resolution_time, 2)
        })

    return {
        "period_days": days,
        "data": performance_data
    }


@router.get("/export")
async def export_tickets(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Export tickets data for reporting."""
    query = db.query(Ticket)

    if start_date:
        query = query.filter(Ticket.created_at >= start_date)
    if end_date:
        query = query.filter(Ticket.created_at <= end_date)
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)

    tickets = query.all()

    export_data = []
    for ticket in tickets:
        export_data.append({
            "ticket_number": ticket.ticket_number,
            "title": ticket.title,
            "status": ticket.status.value,
            "priority": ticket.priority.value,
            "created_by": ticket.creator.username if ticket.creator else None,
            "assigned_to": ticket.assignee.username if ticket.assignee else None,
            "created_at": ticket.created_at.isoformat(),
            "resolved_at": ticket.resolved_at.isoformat() if ticket.resolved_at else None,
            "sla_breached": ticket.sla_response_breached or ticket.sla_resolution_breached
        })

    return {
        "total_records": len(export_data),
        "data": export_data
    }
