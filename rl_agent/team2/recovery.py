"""
recovery.py - Cross-Traffic Recovery & Queue Flush Management

Manages signal recovery after an emergency vehicle passes a junction.
Flushes accumulated cross-traffic queues for a controlled, safe duration
before releasing control back to B1 Q-learning.
"""

import logging
from typing import Dict, Optional, Any
from rl_agent.team2.emergency_config import FLUSH_TIME_PER_LANE, MIN_GREEN_DURATION
from rl_agent.team2.traci_adapter import get_traci_adapter, TraCIAdapter

logger = logging.getLogger(__name__)


class RecoveryManager:
    """
    Manages cross-traffic recovery and queue flushing post-emergency preemption.
    """

    def __init__(self, flush_time_per_lane: float = FLUSH_TIME_PER_LANE):
        self.flush_time_per_lane = flush_time_per_lane
        self.active_recoveries: Dict[str, Dict[str, float]] = {}

    def calculate_flush_time(self, cross_traffic_queues: Dict[str, int]) -> float:
        if not cross_traffic_queues:
            return MIN_GREEN_DURATION

        max_queue = max(cross_traffic_queues.values()) if cross_traffic_queues else 0
        flush_duration = max(MIN_GREEN_DURATION, min(60.0, max_queue * 2.5))
        return round(flush_duration, 1)

    def start_recovery(
        self,
        junction_id: str,
        tls_id: str,
        cross_traffic_queues: Optional[Dict[str, int]] = None,
        current_time: float = 0.0,
        traci_interface: Optional[Any] = None
    ) -> float:
        queues = cross_traffic_queues or {}
        duration = self.calculate_flush_time(queues)

        self.active_recoveries[junction_id] = {
            "start_time": current_time,
            "duration": duration,
        }

        adapter: TraCIAdapter = get_traci_adapter(traci_interface)
        flush_phase = 2  # default cross-traffic flush phase
        try:
            adapter.force_phase_change(tls_id, flush_phase)
        except Exception as e:
            logger.error(f"Failed to force recovery flush phase on {junction_id}: {e}")

        logger.info(
            f"[RECOVERY] Starting recovery on junction {junction_id} "
            f"(Allocated Flush Duration: {duration}s)."
        )
        return duration

    def is_recovering(self, junction_id: str, current_time: float) -> bool:
        if junction_id not in self.active_recoveries:
            return False
        return not self.is_recovery_complete(junction_id, current_time)

    def is_recovery_complete(self, junction_id: str, current_time: float) -> bool:
        if junction_id not in self.active_recoveries:
            return True

        rec_info = self.active_recoveries[junction_id]
        elapsed = current_time - rec_info["start_time"]
        complete = elapsed >= rec_info["duration"]

        if complete:
            del self.active_recoveries[junction_id]
            logger.info(f"[RECOVERY] Recovery complete on junction {junction_id}.")

        return complete
