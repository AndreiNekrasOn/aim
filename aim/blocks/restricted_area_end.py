# blocks/restricted_area_end.py

from typing import Optional, TYPE_CHECKING
from ..core.block import BaseBlock
from ..core.agent import BaseAgent
from ..core.simulator import Simulator

if TYPE_CHECKING:
    from . import RestrictedAreaStart

class RestrictedAreaEnd(BaseBlock):
    """
    Marks exit from a restricted area.
    Must be paired with a RestrictedAreaStart.
    Notifies start block to free up a slot.
    """

    def __init__(self, simulator: 'Simulator', start_block: 'RestrictedAreaStart'):
        super().__init__(simulator)
        self.start_block = start_block
        # Back-reference is set by start_block.set_end()
        self._linked_start: Optional['RestrictedAreaStart'] = None

    def _set_start(self, start_block: 'RestrictedAreaStart') -> None:
        """Internal: called by start_block.set_end() to ensure bidirectional link."""
        self._linked_start = start_block

    def take(self, agent: BaseAgent) -> None:
        """Agent exits restricted area — notify start block."""
        agent._enter_block(self)

        # Discover which start block this agent belongs to
        start_block = getattr(agent, '_restricted_area_start', None)

        if start_block is None:
            # Fallback: use the start_block passed in constructor
            start_block = self.start_block
            print(f"WARNING: Agent {id(agent)} has no _restricted_area_start. Using constructor default.")

        if start_block != self.start_block:
            print(f"WARNING: Agent {id(agent)} entered via different start block.")

        # Notify start block
        start_block._on_agent_exit(agent)

        # Clear agent metadata
        if hasattr(agent, '_restricted_area_start'):
            delattr(agent, '_restricted_area_start')

        self._eject(agent)

