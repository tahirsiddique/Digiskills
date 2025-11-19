"""Enhanced ticket management API routes with email, SLA, and search."""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from database import get_db
from models import User, Ticket, TicketStatus, TicketPriority, UserRole, SLAPolicy
from schemas import TicketCreate, TicketUpdate, TicketResponse, TicketSearchParams
from auth import get_current_user, require_technician
from email_service import email_service

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


def generate_ticket_number(db: Session) -> str:
    """Generate unique ticket number."""
    latest_ticket = db.query(Ticket).order_by(Ticket.id.desc()).first()

    if latest_ticket:
        try:
            last_num = int(latest_ticket.ticket_number.split("-")[1])
            new_num = last_num + 1
        except (IndexError, ValueError):
            new_num = 1
    else:
        new_num = 1

    return f"TKT-{new_num:05d}"


def apply_sla_policy(ticket: Ticket, db: Session):
    """Apply SLA policy to ticket based on priority."""
    # Find active SLA policy matching the ticket priority
    sla_policy = db.query(SLAPolicy).filter(
        SLAPolicy.priority == ticket.priority.value,
        SLAPolicy.is_active == True
    ).first()

    if sla_policy:
        ticket.sla_policy_id = sla_policy.id
        ticket.sla_response_due = ticket.created_at + timedelta(hours=sla_policy.response_time_hours)
        ticket.sla_resolution_due = ticket.created_at + timedelta(hours=sla_policy.resolution_time_hours)


def check_sla_breach(ticket: Ticket):
    """Check and update SLA breach status."""
    now = datetime.utcnow()

    # Check response SLA
    if ticket.sla_response_due and not ticket.first_response_at:
        if now > ticket.sla_response_due:
            ticket.sla_response_breached = True

    # Check resolution SLA
    if ticket.sla_resolution_due and ticket.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
        if now > ticket.sla_resolution_due:
            ticket.sla_resolution_breached = True


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new ticket with email notification and SLA tracking."""
    ticket = Ticket(
        ticket_number=generate_ticket_number(db),
        title=ticket_data.title,
        description=ticket_data.description,
        priority=ticket_data.priority,
        category_id=ticket_data.category_id,
        created_by=current_user.id,
        status=TicketStatus.NEW
    )

    # Apply SLA policy
    apply_sla_policy(ticket, db)

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # Send email notification to creator
    await email_service.send_ticket_created_notification(
        ticket_number=ticket.ticket_number,
        ticket_id=ticket.id,
        title=ticket.title,
        creator_email=current_user.email,
        creator_name=current_user.first_name or current_user.username
    )

    return ticket


@router.get("/search", response_model=List[TicketResponse])
async def search_tickets(
    query: Optional[str] = None,
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    category_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    created_by: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sla_breached: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Advanced ticket search with multiple filters."""
    ticket_query = db.query(Ticket)

    # Regular users can only search their own tickets
    if current_user.role == UserRole.USER:
        ticket_query = ticket_query.filter(
            or_(
                Ticket.created_by == current_user.id,
                Ticket.assigned_to == current_user.id
            )
        )

    # Full-text search on title and description
    if query:
        search_filter = or_(
            Ticket.title.ilike(f"%{query}%"),
            Ticket.description.ilike(f"%{query}%"),
            Ticket.ticket_number.ilike(f"%{query}%")
        )
        ticket_query = ticket_query.filter(search_filter)

    # Apply filters
    if status:
        ticket_query = ticket_query.filter(Ticket.status == status)
    if priority:
        ticket_query = ticket_query.filter(Ticket.priority == priority)
    if category_id:
        ticket_query = ticket_query.filter(Ticket.category_id == category_id)
    if assigned_to:
        ticket_query = ticket_query.filter(Ticket.assigned_to == assigned_to)
    if created_by:
        ticket_query = ticket_query.filter(Ticket.created_by == created_by)
    if date_from:
        ticket_query = ticket_query.filter(Ticket.created_at >= date_from)
    if date_to:
        ticket_query = ticket_query.filter(Ticket.created_at <= date_to)
    if sla_breached is not None:
        if sla_breached:
            ticket_query = ticket_query.filter(
                or_(
                    Ticket.sla_response_breached == True,
                    Ticket.sla_resolution_breached == True
                )
            )

    tickets = ticket_query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()

    # Update SLA breach status for each ticket
    for ticket in tickets:
        check_sla_breach(ticket)

    db.commit()

    return tickets


@router.get("", response_model=List[TicketResponse])
async def list_tickets(
    skip: int = 0,
    limit: int = 100,
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    assigned_to_me: bool = False,
    created_by_me: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List tickets with filters."""
    query = db.query(Ticket)

    # Regular users can only see their own tickets
    if current_user.role == UserRole.USER:
        query = query.filter(
            or_(
                Ticket.created_by == current_user.id,
                Ticket.assigned_to == current_user.id
            )
        )
    else:
        # Technicians and admins can see all tickets or filter
        if assigned_to_me:
            query = query.filter(Ticket.assigned_to == current_user.id)
        if created_by_me:
            query = query.filter(Ticket.created_by == current_user.id)

    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)

    tickets = query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()

    # Update SLA breach status
    for ticket in tickets:
        check_sla_breach(ticket)

    db.commit()

    return tickets


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ticket by ID."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Check permissions
    if current_user.role == UserRole.USER:
        if ticket.created_by != current_user.id and ticket.assigned_to != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this ticket"
            )

    # Update SLA breach status
    check_sla_breach(ticket)
    db.commit()

    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update ticket with email notifications."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Check permissions
    if current_user.role == UserRole.USER:
        if ticket.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this ticket"
            )
        # Regular users can't assign tickets or change certain fields
        ticket_data.assigned_to = None
        ticket_data.status = None

    # Store old status for email notification
    old_status = ticket.status

    # Update fields
    update_data = ticket_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None:
            setattr(ticket, field, value)

    # Update timestamps based on status
    if ticket_data.status == TicketStatus.RESOLVED and not ticket.resolved_at:
        ticket.resolved_at = datetime.utcnow()
    elif ticket_data.status == TicketStatus.CLOSED and not ticket.closed_at:
        ticket.closed_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)

    # Send status change email notification
    if ticket_data.status and ticket_data.status != old_status:
        creator = db.query(User).filter(User.id == ticket.created_by).first()
        if creator:
            await email_service.send_ticket_status_changed_notification(
                ticket_number=ticket.ticket_number,
                ticket_id=ticket.id,
                title=ticket.title,
                old_status=old_status.value,
                new_status=ticket.status.value,
                user_email=creator.email,
                user_name=creator.first_name or creator.username
            )

    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Delete ticket (technician/admin only)."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    db.delete(ticket)
    db.commit()


@router.post("/{ticket_id}/assign", response_model=TicketResponse)
async def assign_ticket(
    ticket_id: int,
    assignee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Assign ticket to a technician with email notification."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Verify assignee exists and is a technician
    assignee = db.query(User).filter(User.id == assignee_id).first()
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignee not found"
        )

    if assignee.role not in [UserRole.TECHNICIAN, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only assign to technicians or admins"
        )

    ticket.assigned_to = assignee_id
    ticket.status = TicketStatus.ASSIGNED

    db.commit()
    db.refresh(ticket)

    # Send email notification to assignee
    await email_service.send_ticket_assigned_notification(
        ticket_number=ticket.ticket_number,
        ticket_id=ticket.id,
        title=ticket.title,
        assignee_email=assignee.email,
        assignee_name=assignee.first_name or assignee.username,
        priority=ticket.priority.value
    )

    return ticket
