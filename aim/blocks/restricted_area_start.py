# blocks/restricted_area_start.py

from typing import List, Optional, TYPE_CHECKING
from ..core.block import BaseBlock
from ..core.agent import BaseAgent
from ..core.simulator import Simulator
from . import QueueBlock

if TYPE_CHECKING:
    from . import RestrictedAreaEnd

class RestrictedAreaStart(BaseBlock):
    """
    Controls entry into a restricted area.
    Only allows N agents between Start and End at any time.
    Must be paired with a RestrictedAreaEnd.
    """

    def __init__(self, simulator: 'Simulator', max_agents: int = 1):
        super().__init__(simulator)
        self.max_agents = max_agents
        self.current_agents = 0
        self.end_block: Optional['RestrictedAreaEnd'] = None
        self._waiting_agents: List[BaseAgent] = []

    def set_end(self, end_block: 'RestrictedAreaEnd') -> None:
        """Bind this start to an end block."""
        if self.end_block is not None:
            raise ValueError("End block already set.")
        self.end_block = end_block
        end_block._set_start(self)  # Ensure back-reference

    def take(self, agent: BaseAgent) -> None:
        """
        Accept agent — but ONLY if coming from a QueueBlock.
        Raises RuntimeError if pushed directly by user (e.g., from SourceBlock).
        """
        # Check: agent must be coming from a QueueBlock
        if not isinstance(agent.current_block, QueueBlock):
            raise RuntimeError(
                f"RestrictedAreaStart {id(self)} only accepts agents from QueueBlock. "
                f"Agent {id(agent)} came from {type(agent.current_block).__name__}. "
                f"Place a QueueBlock upstream."
            )

        agent._enter_block(self)
        self._waiting_agents.append(agent)

    def _tick(self) -> None:
        """Try to admit waiting agents."""
        if self.end_block is None:
            # Auto-heal: if no end set, log warning but don't crash
            print(f"WARNING: RestrictedAreaStart {id(self)} has no end block set. Agents will not be released.")
            return

        remaining = []
        for agent in self._waiting_agents:
            if self.current_agents < self.max_agents:
                self.current_agents += 1
                # Mark agent as inside restricted area (optional)
                setattr(agent, '_restricted_area_start', self)
                if self.output_connections and self.output_connections[0]:
                    self.output_connections[0].take(agent)
                self._eject(agent)
            else:
                remaining.append(agent)
        self._waiting_agents = remaining

    def _on_agent_exit(self, agent: BaseAgent) -> None:
        """Called by RestrictedAreaEnd when agent exits."""
        if self.current_agents > 0:
            self.current_agents -= 1
        else:
            print(f"WARNING: RestrictedAreaStart {id(self)} exited agent but count was 0.")

    @property
    def size(self) -> int:
        """Number of agents waiting to enter."""
        return len(self._waiting_agents)

    @property
    def active_agents(self) -> int:
        """Number of agents currently inside restricted area."""
        return self.current_agents
