from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

@dataclass
class CalendarEvent:
    id: str
    title: str
    start: datetime
    end: datetime
    description: Optional[str] = ""
    location: Optional[str] = ""
    color: Optional[str] = "#33b5e5" # Default Google Blue
    is_all_day: bool = False
    
    @property
    def duration(self) -> timedelta:
        return self.end - self.start

class CalendarProvider(ABC):
    """
    Abstract Base Class for Calendar Providers (Google, Outlook, iCloud, Local)
    """
    
    @abstractmethod
    def connect(self) -> bool:
        """Authenticate and connect to the service. Returns True if successful."""
        pass
        
    @abstractmethod
    def get_events(self, start_date: datetime, end_date: datetime) -> List[CalendarEvent]:
        """Fetch events within a range."""
        pass
        
    @abstractmethod
    def create_event(self, event: CalendarEvent) -> bool:
        """Create a new event."""
        pass

class MockCalendarProvider(CalendarProvider):
    """
    Default provider for testing/demo purposes.
    """
    def connect(self) -> bool:
        return True
        
    def get_events(self, start_date: datetime, end_date: datetime) -> List[CalendarEvent]:
        # Return some fake events
        now = datetime.now()
        events = [
            CalendarEvent(
                id="1", 
                title="Mock Meeting", 
                start=now.replace(hour=10, minute=0), 
                end=now.replace(hour=11, minute=0),
                description="This is a fake meeting."
            ),
            CalendarEvent(
                id="2", 
                title="Lunch Break", 
                start=now.replace(hour=13, minute=0), 
                end=now.replace(hour=14, minute=0),
                color="#e53333"
            )
        ]
        return events
        
    def create_event(self, event: CalendarEvent) -> bool:
        print(f"Mock created event: {event.title}")
        return True
