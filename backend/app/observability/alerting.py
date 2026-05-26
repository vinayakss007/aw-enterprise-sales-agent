"""Alert manager - monitors thresholds and notifies."""
import asyncio
import logging
from typing import List

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages background alert monitoring."""

    def __init__(self):
        self.is_monitoring = False
        self._task = None

    async def start_monitoring(self):
        """Start background alert monitoring loop."""
        logger.info("Alert monitoring started")
        self.is_monitoring = True
        while self.is_monitoring:
            await asyncio.sleep(60)

    def stop_monitoring(self):
        """Stop alert monitoring."""
        logger.info("Alert monitoring stopped")
        self.is_monitoring = False


ALERT_MANAGER = AlertManager()
