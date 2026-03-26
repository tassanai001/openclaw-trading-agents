"""
Configuration for the Learning Agent
"""
import os
from dataclasses import dataclass


@dataclass
class LearningConfig:
    """Configuration class for Learning Agent"""
    reports_directory: str = "reports/learning"
    max_history_records: int = 1000
    report_timezone: str = "UTC"
    enable_notifications: bool = False
    notification_threshold: float = 0.05  # 5% threshold for notifications
    export_format: str = "markdown"  # Options: markdown, json, csv
    
    def __post_init__(self):
        """Create reports directory if it doesn't exist"""
        os.makedirs(self.reports_directory, exist_ok=True)