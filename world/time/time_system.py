"""
Time system for overworld.

Tracks time progression for the overworld.
"""


class TimeSystem:
    """
    Simple time tracking system.
    
    Tracks days, hours, and minutes.
    """
    
    def __init__(self, days: int = 0, hours: int = 0, minutes: int = 0) -> None:
        """
        Initialize time system.
        
        Args:
            days: Starting day
            hours: Starting hour (0-23)
            minutes: Starting minute (0-59)
        """
        self.days = days
        self.hours = max(0, min(23, hours))
        self.minutes = max(0, min(59, minutes))
    
    def add_time(self, hours: float) -> None:
        """
        Add time to the system.
        
        Args:
            hours: Hours to add (can be fractional)
        """
        # Convert to minutes for precision
        total_minutes = self.minutes + int(hours * 60)
        
        # Calculate new time
        self.minutes = total_minutes % 60
        hours_to_add = total_minutes // 60
        self.hours += hours_to_add
        
        # Roll over days
        if self.hours >= 24:
            self.days += self.hours // 24
            self.hours = self.hours % 24
    
    def get_time_string(self) -> str:
        """Get formatted time string."""
        return f"Day {self.days + 1}, {self.hours:02d}:{self.minutes:02d}"
    
    def is_daytime(self) -> bool:
        """Check if it's daytime (6:00 to 20:00)."""
        return 6 <= self.hours < 20
    
    def get_time_of_day(self) -> str:
        """Get time of day description."""
        if 5 <= self.hours < 8:
            return "dawn"
        elif 8 <= self.hours < 18:
            return "day"
        elif 18 <= self.hours < 21:
            return "dusk"
        else:
            return "night"

