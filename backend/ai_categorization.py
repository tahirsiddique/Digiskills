"""AI-powered ticket categorization service."""
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from models import Category, Ticket, TicketPriority
import re


class AICategorizationService:
    """Service for AI-powered ticket categorization."""

    # Keyword mappings for categories
    CATEGORY_KEYWORDS = {
        "Hardware": [
            "computer", "laptop", "desktop", "monitor", "keyboard", "mouse",
            "printer", "scanner", "hardware", "device", "screen", "display",
            "broken", "physical", "cable", "port", "usb", "hdmi"
        ],
        "Software": [
            "software", "application", "app", "program", "install", "uninstall",
            "update", "upgrade", "bug", "error", "crash", "freeze", "slow",
            "windows", "mac", "linux", "office", "excel", "word", "outlook"
        ],
        "Network": [
            "network", "internet", "wifi", "wi-fi", "connection", "disconnect",
            "vpn", "ethernet", "router", "switch", "firewall", "dns", "ip",
            "speed", "slow internet", "no internet", "cannot connect"
        ],
        "Account": [
            "account", "password", "login", "access", "permission", "username",
            "email", "reset", "forgot", "locked", "disabled", "authentication",
            "credentials", "sign in", "log in"
        ]
    }

    # Priority keywords
    PRIORITY_KEYWORDS = {
        TicketPriority.CRITICAL: [
            "critical", "urgent", "emergency", "down", "outage", "broken",
            "not working", "cannot work", "production down", "all users",
            "company-wide", "asap", "immediately"
        ],
        TicketPriority.HIGH: [
            "high", "important", "priority", "soon", "blocking", "major",
            "multiple users", "department", "team"
        ],
        TicketPriority.MEDIUM: [
            "medium", "normal", "standard", "regular"
        ],
        TicketPriority.LOW: [
            "low", "minor", "small", "cosmetic", "enhancement", "feature request",
            "when possible", "not urgent"
        ]
    }

    def suggest_category(self, title: str, description: str, db: Session) -> Optional[Category]:
        """Suggest category based on ticket content."""
        # Combine title and description for analysis
        content = f"{title} {description}".lower()

        # Score each category
        scores = {}
        categories = db.query(Category).all()
        category_map = {cat.name: cat for cat in categories}

        for category_name, keywords in self.CATEGORY_KEYWORDS.items():
            if category_name in category_map:
                score = sum(1 for keyword in keywords if keyword in content)
                if score > 0:
                    scores[category_name] = score

        # Return category with highest score
        if scores:
            best_category = max(scores, key=scores.get)
            return category_map.get(best_category)

        return None

    def suggest_priority(self, title: str, description: str) -> TicketPriority:
        """Suggest priority based on ticket content."""
        content = f"{title} {description}".lower()

        # Check for critical keywords first
        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            keyword_count = sum(1 for keyword in keywords if keyword in content)
            if keyword_count > 0:
                return priority

        # Default to medium if no keywords matched
        return TicketPriority.MEDIUM

    def analyze_ticket(
        self,
        title: str,
        description: str,
        db: Session
    ) -> Dict[str, any]:
        """Analyze ticket and provide suggestions."""
        suggested_category = self.suggest_category(title, description, db)
        suggested_priority = self.suggest_priority(title, description)

        # Extract potential tags
        tags = self.extract_tags(f"{title} {description}")

        # Detect sentiment/urgency
        urgency_score = self.calculate_urgency(title, description)

        return {
            "suggested_category_id": suggested_category.id if suggested_category else None,
            "suggested_category_name": suggested_category.name if suggested_category else None,
            "suggested_priority": suggested_priority.value,
            "urgency_score": urgency_score,
            "suggested_tags": tags[:5],  # Top 5 tags
            "confidence": self.calculate_confidence(title, description, suggested_category)
        }

    def extract_tags(self, content: str) -> List[str]:
        """Extract potential tags from content."""
        content = content.lower()
        tags = []

        # Extract common IT terms
        it_terms = [
            "password", "email", "vpn", "printer", "wifi", "network",
            "software", "hardware", "access", "login", "installation",
            "update", "error", "crash", "slow", "backup"
        ]

        for term in it_terms:
            if term in content:
                tags.append(term)

        return tags

    def calculate_urgency(self, title: str, description: str) -> float:
        """Calculate urgency score (0-1)."""
        content = f"{title} {description}".lower()

        urgent_words = [
            "urgent", "emergency", "critical", "asap", "immediately",
            "down", "broken", "not working", "cannot", "unable"
        ]

        urgency_count = sum(1 for word in urgent_words if word in content)

        # Normalize to 0-1 scale
        max_urgency = 5
        return min(urgency_count / max_urgency, 1.0)

    def calculate_confidence(
        self,
        title: str,
        description: str,
        suggested_category: Optional[Category]
    ) -> float:
        """Calculate confidence level for suggestions (0-1)."""
        if not suggested_category:
            return 0.0

        content = f"{title} {description}".lower()

        # Get keywords for suggested category
        keywords = self.CATEGORY_KEYWORDS.get(suggested_category.name, [])

        # Count matches
        matches = sum(1 for keyword in keywords if keyword in content)

        # Normalize confidence
        if len(keywords) == 0:
            return 0.5

        confidence = min(matches / 3, 1.0)  # 3+ matches = 100% confidence
        return round(confidence, 2)


# Global AI categorization service instance
ai_service = AICategorizationService()
