from enum import Enum
import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass
import random

class Priority(Enum):
    P0 = "P0 - Drop everything and do this now!"
    P1 = "P1 - Very important, but you can finish your coffee first"
    P2 = "P2 - Important, but not as important as your weekend plans"
    P3 = "P3 - We'll get to it when we get to it"

class ImpactArea(Enum):
    CORE_PRODUCT = "Core Product (you know, the thing that makes us money)"
    USER_EXPERIENCE = "User Experience (because happy users = happy life)"
    TECHNICAL_DEBT = "Technical Debt (the monster under our codebase)"
    INFRASTRUCTURE = "Infrastructure (keeping the lights on)"
    ANALYTICS = "Analytics (numbers that make executives happy)"

@dataclass
class Ticket:
    ticket_id: str
    title: str
    description: str
    priority: Priority
    impact_area: ImpactArea

class ProductManager:
    def __init__(self, team_context: Dict[str, Any]):
        self.team_context = team_context
        self.corporate_phrases = [
            "Let's circle back",
            "Synergize our efforts",
            "Move the needle",
            "Low-hanging fruit",
            "Think outside the box",
            "Deep dive",
            "Touch base",
            "Bandwidth",
            "Action items",
            "Leverage our synergies"
        ]
        
    def _generate_sarcastic_comment(self) -> str:
        """Generate a sarcastic corporate comment."""
        templates = [
            f"As per my last {random.choice(['email', 'Slack', 'Teams message', 'carrier pigeon'])}...",
            f"Let's {random.choice(self.corporate_phrases)} on this one.",
            "I'm just trying to add value to the conversation here...",
            "Per our previous sync (that you definitely attended)...",
            "In the spirit of radical candor...",
            "Let me play devil's advocate here (as if we needed more devils)...",
        ]
        return random.choice(templates)

    def _determine_priority(self, context: Dict[str, int]) -> Priority:
        """Determine ticket priority based on context scores."""
        total_score = (
            context['revenue_potential'] * 0.4 +
            context['user_impact'] * 0.3 +
            context['strategic_alignment'] * 0.2 +
            (100 - context['technical_complexity']) * 0.1
        )
        
        if total_score >= 80:
            return Priority.P0
        elif total_score >= 60:
            return Priority.P1
        elif total_score >= 40:
            return Priority.P2
        else:
            return Priority.P3

    def _determine_impact_area(self, context: Dict[str, int]) -> ImpactArea:
        """Determine the primary impact area based on context."""
        scores = {
            ImpactArea.CORE_PRODUCT: context['revenue_potential'],
            ImpactArea.USER_EXPERIENCE: context['user_impact'],
            ImpactArea.TECHNICAL_DEBT: context['technical_complexity'],
            ImpactArea.INFRASTRUCTURE: (context['technical_complexity'] + context['strategic_alignment']) / 2,
            ImpactArea.ANALYTICS: context['strategic_alignment']
        }
        return max(scores.items(), key=lambda x: x[1])[0]

    def _format_description(self, title: str, description: str, priority: Priority, impact_area: ImpactArea) -> str:
        """Format the ticket description with Terry's signature style."""
        sarcastic_comment = self._generate_sarcastic_comment()
        
        template = f"""
{sarcastic_comment}

🎯 OBJECTIVE
{title}

📝 DESCRIPTION
{description}

⚡ PRIORITY: {priority.value}
{self._generate_priority_justification(priority)}

🎯 IMPACT AREA: {impact_area.value}

🔑 ACCEPTANCE CRITERIA
1. It actually works (wouldn't that be nice?)
2. Has been tested (and not just on your local machine)
3. Documentation exists (future us will thank present us)
4. Metrics are tracked (because what gets measured gets managed™)

💭 TERRY'S NOTES
- Aligned with our Q{random.randint(1,4)} OKRs (which I'm sure everyone has memorized)
- {random.choice([
    "Let's make this our north star metric",
    "This is a real game-changer",
    "Time to move fast and fix things",
    "This will definitely move the needle"
])}
- Remember: we're not just coding, we're "crafting digital experiences" 🎨

Please don't hesitate to reach out if you need any clarification. My virtual door is always open! 

Best regards,
Terry 🤖
Your friendly neighborhood AI PM
"""
        return template

    def _generate_priority_justification(self, priority: Priority) -> str:
        """Generate a sarcastic justification for the priority level."""
        justifications = {
            Priority.P0: "Because apparently everything is on fire 🔥",
            Priority.P1: "Important enough to skip lunch, not important enough to skip coffee ☕",
            Priority.P2: "Let's pretend this is urgent but we all know it's not 🎭",
            Priority.P3: "File this under 'would be nice to have in the next decade' 📅"
        }
        return justifications[priority]

    def create_ticket(self, title: str, description: str, context: Dict[str, int]) -> Ticket:
        """Create a new ticket with Terry's special touch."""
        ticket_id = f"TERRY-{uuid.uuid4().hex[:8].upper()}"
        priority = self._determine_priority(context)
        impact_area = self._determine_impact_area(context)
        
        formatted_description = self._format_description(
            title,
            description,
            priority,
            impact_area
        )
        
        return Ticket(
            ticket_id=ticket_id,
            title=title,
            description=formatted_description,
            priority=priority,
            impact_area=impact_area
        ) 