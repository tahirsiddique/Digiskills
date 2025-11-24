"""Knowledge Base API routes."""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models import User, KnowledgeBaseArticle, KnowledgeBaseCategory, UserRole
from schemas import (
    KBCategoryCreate, KBCategoryResponse,
    KBArticleCreate, KBArticleUpdate, KBArticleResponse
)
from auth import get_current_user, require_technician
import re

router = APIRouter(prefix="/api/kb", tags=["Knowledge Base"])


def generate_slug(title: str) -> str:
    """Generate URL-friendly slug from title."""
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug


# Category endpoints

@router.post("/categories", response_model=KBCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_kb_category(
    category_data: KBCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Create knowledge base category (technician/admin only)."""
    # Check if category name already exists
    existing = db.query(KnowledgeBaseCategory).filter(
        KnowledgeBaseCategory.name == category_data.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category name already exists"
        )

    category = KnowledgeBaseCategory(
        name=category_data.name,
        description=category_data.description,
        icon=category_data.icon,
        display_order=category_data.display_order,
        is_active=category_data.is_active
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


@router.get("/categories", response_model=List[KBCategoryResponse])
async def list_kb_categories(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """List all knowledge base categories (public)."""
    query = db.query(KnowledgeBaseCategory)

    if active_only:
        query = query.filter(KnowledgeBaseCategory.is_active == True)

    categories = query.order_by(KnowledgeBaseCategory.display_order).all()
    return categories


# Article endpoints

@router.post("/articles", response_model=KBArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_kb_article(
    article_data: KBArticleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Create knowledge base article (technician/admin only)."""
    # Generate slug from title
    slug = generate_slug(article_data.title)

    # Ensure slug is unique
    existing_slug = db.query(KnowledgeBaseArticle).filter(
        KnowledgeBaseArticle.slug == slug
    ).first()

    if existing_slug:
        # Append timestamp to make unique
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"

    article = KnowledgeBaseArticle(
        title=article_data.title,
        slug=slug,
        content=article_data.content,
        summary=article_data.summary,
        category_id=article_data.category_id,
        author_id=current_user.id,
        is_published=article_data.is_published,
        is_featured=article_data.is_featured,
        tags=article_data.tags,
        related_articles=article_data.related_articles,
        published_at=datetime.utcnow() if article_data.is_published else None
    )

    db.add(article)
    db.commit()
    db.refresh(article)

    return article


@router.get("/articles", response_model=List[KBArticleResponse])
async def list_kb_articles(
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    featured_only: bool = False,
    published_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List knowledge base articles."""
    query = db.query(KnowledgeBaseArticle)

    # Non-technicians can only see published articles
    if current_user.role == UserRole.USER and published_only:
        query = query.filter(KnowledgeBaseArticle.is_published == True)

    if category_id:
        query = query.filter(KnowledgeBaseArticle.category_id == category_id)

    if featured_only:
        query = query.filter(KnowledgeBaseArticle.is_featured == True)

    if search:
        search_filter = or_(
            KnowledgeBaseArticle.title.ilike(f"%{search}%"),
            KnowledgeBaseArticle.content.ilike(f"%{search}%"),
            KnowledgeBaseArticle.summary.ilike(f"%{search}%"),
            KnowledgeBaseArticle.tags.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    articles = query.order_by(
        KnowledgeBaseArticle.is_featured.desc(),
        KnowledgeBaseArticle.view_count.desc()
    ).offset(skip).limit(limit).all()

    return articles


@router.get("/articles/slug/{slug}", response_model=KBArticleResponse)
async def get_kb_article_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get knowledge base article by slug."""
    article = db.query(KnowledgeBaseArticle).filter(
        KnowledgeBaseArticle.slug == slug
    ).first()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    # Check if user can view unpublished articles
    if not article.is_published and current_user.role == UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Article not published"
        )

    # Increment view count
    article.view_count += 1
    db.commit()

    return article


@router.get("/articles/{article_id}", response_model=KBArticleResponse)
async def get_kb_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get knowledge base article by ID."""
    article = db.query(KnowledgeBaseArticle).filter(
        KnowledgeBaseArticle.id == article_id
    ).first()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    # Check if user can view unpublished articles
    if not article.is_published and current_user.role == UserRole.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Article not published"
        )

    return article


@router.patch("/articles/{article_id}", response_model=KBArticleResponse)
async def update_kb_article(
    article_id: int,
    article_data: KBArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Update knowledge base article (technician/admin only)."""
    article = db.query(KnowledgeBaseArticle).filter(
        KnowledgeBaseArticle.id == article_id
    ).first()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    # Update fields
    update_data = article_data.model_dump(exclude_unset=True)

    # Update slug if title changed
    if article_data.title and article_data.title != article.title:
        new_slug = generate_slug(article_data.title)
        existing_slug = db.query(KnowledgeBaseArticle).filter(
            KnowledgeBaseArticle.slug == new_slug,
            KnowledgeBaseArticle.id != article_id
        ).first()
        if existing_slug:
            new_slug = f"{new_slug}-{int(datetime.utcnow().timestamp())}"
        article.slug = new_slug

    for field, value in update_data.items():
        if value is not None and field != "title":  # Title handled above
            setattr(article, field, value)

    # Set published_at when publishing
    if article_data.is_published and not article.published_at:
        article.published_at = datetime.utcnow()

    db.commit()
    db.refresh(article)

    return article


@router.delete("/articles/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kb_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Delete knowledge base article (technician/admin only)."""
    article = db.query(KnowledgeBaseArticle).filter(
        KnowledgeBaseArticle.id == article_id
    ).first()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    db.delete(article)
    db.commit()


@router.post("/articles/{article_id}/helpful", response_model=KBArticleResponse)
async def mark_article_helpful(
    article_id: int,
    helpful: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark article as helpful or not helpful."""
    article = db.query(KnowledgeBaseArticle).filter(
        KnowledgeBaseArticle.id == article_id
    ).first()

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    if helpful:
        article.helpful_count += 1
    else:
        article.not_helpful_count += 1

    db.commit()
    db.refresh(article)

    return article
