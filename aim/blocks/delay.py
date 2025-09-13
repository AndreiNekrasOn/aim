# blocks/delay.py

from typing import Dict, List
from ..core.block import BaseBlock
from ..core.agent import BaseAgent
from ..core.simulator import Simulator

class DelayBlock(BaseBlock):
    """
    Holds each agent for a fixed number of ticks, then ejects to next block.
    Uses scheduled events for precision and efficiency.
    No internal polling. No per-tick scans.
    """

    def __init__(self, simulator: 'Simulator', delay_ticks: int = 1):
        """
        :param simulator: The simulator this block belongs to.
        :param delay_ticks: Number of ticks to hold each agent.
        """
        super().__init__(simulator)
        self.delay_ticks = delay_ticks
        # Track scheduled ejection tick per agent (optional — for inspection)
        self._scheduled_ejections: Dict[BaseAgent, int] = {}

    def take(self, agent: BaseAgent) -> None:
        """
        Accept agent immediately. Schedule its ejection.
        """
        agent._enter_block(self)
        if self.on_enter is not None:
            self.on_enter(agent)
        # Schedule ejection at current_tick + delay_ticks
        eject_tick = self._simulator.current_tick + self.delay_ticks
        self._scheduled_ejections[agent] = eject_tick

        # Use simulator's event scheduler
        self._simulator.schedule_event(
            callback=lambda tick: self._eject_agent(agent),
            delay_ticks=self.delay_ticks,
            recurring=False
        )

    def _eject_agent(self, agent: BaseAgent) -> None:
        """
        Internal: eject agent to next block.
        Called by scheduled event.
        """
        # Safety: agent may have been removed (e.g., sim stopped)
        if agent not in self._scheduled_ejections:
            return

        del self._scheduled_ejections[agent]

        self._eject(agent)

    @property
    def size(self) -> int:
        """Number of agents currently being delayed."""
        return len(self._scheduled_ejections)
