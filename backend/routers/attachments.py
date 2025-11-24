"""File attachment API routes."""
import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from models import User, Ticket, TicketAttachment, UserRole
from schemas import AttachmentResponse
from auth import get_current_user
from config import settings

router = APIRouter(prefix="/api/attachments", tags=["Attachments"])


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to start

    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
        )

    # Check file extension
    file_ext = os.path.splitext(file.filename)[1][1:].lower()
    if file_ext not in settings.allowed_file_types_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type .{file_ext} not allowed. Allowed types: {', '.join(settings.allowed_file_types_list)}"
        )


def save_upload_file(upload_file: UploadFile, ticket_id: int) -> tuple[str, str]:
    """Save uploaded file and return (file_path, original_filename)."""
    # Create ticket-specific directory
    ticket_dir = os.path.join(settings.UPLOAD_DIR, str(ticket_id))
    os.makedirs(ticket_dir, exist_ok=True)

    # Generate unique filename
    file_ext = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(ticket_dir, unique_filename)

    # Save file
    with open(file_path, "wb") as buffer:
        buffer.write(upload_file.file.read())

    return file_path, upload_file.filename


@router.post("/ticket/{ticket_id}", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    ticket_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a file attachment to a ticket."""
    # Verify ticket exists
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Check if user has access to the ticket
    if current_user.role == UserRole.USER:
        if ticket.created_by != current_user.id and ticket.assigned_to != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload files to this ticket"
            )

    # Validate file
    validate_file(file)

    # Save file
    file_path, original_filename = save_upload_file(file, ticket_id)

    # Get file size
    file_size = os.path.getsize(file_path)

    # Create attachment record
    attachment = TicketAttachment(
        ticket_id=ticket_id,
        file_name=original_filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        uploaded_by=current_user.id
    )

    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    return attachment


@router.get("/ticket/{ticket_id}", response_model=List[AttachmentResponse])
async def list_ticket_attachments(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all attachments for a ticket."""
    # Verify ticket exists
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Check if user has access to the ticket
    if current_user.role == UserRole.USER:
        if ticket.created_by != current_user.id and ticket.assigned_to != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view attachments for this ticket"
            )

    attachments = db.query(TicketAttachment).filter(TicketAttachment.ticket_id == ticket_id).all()
    return attachments


@router.get("/{attachment_id}/download")
async def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download an attachment file."""
    attachment = db.query(TicketAttachment).filter(TicketAttachment.id == attachment_id).first()

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )

    # Check if user has access to the ticket
    ticket = attachment.ticket
    if current_user.role == UserRole.USER:
        if ticket.created_by != current_user.id and ticket.assigned_to != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to download this attachment"
            )

    # Check if file exists
    if not os.path.exists(attachment.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )

    return FileResponse(
        path=attachment.file_path,
        filename=attachment.file_name,
        media_type=attachment.mime_type
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an attachment."""
    attachment = db.query(TicketAttachment).filter(TicketAttachment.id == attachment_id).first()

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )

    # Only attachment uploader or admin can delete
    if attachment.uploaded_by != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this attachment"
        )

    # Delete file from filesystem
    if os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)

    db.delete(attachment)
    db.commit()
