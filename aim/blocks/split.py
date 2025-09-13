# blocks/split.py

from typing import List, Optional
from ..core.block import BaseBlock
from ..core.agent import BaseAgent

class SplitBlock(BaseBlock):
    """
    Splits a container agent into its children agents.
    - Accepts one container agent.
    - Ejects the container (now empty) to first output.
    - Ejects each child agent to second output.
    - Container must have children_agents list (set by CombineBlock).
    """

    def __init__(self, simulator: 'Simulator'):
        super().__init__(simulator)
        self._first_output: Optional[BaseBlock] = None
        self._second_output: Optional[BaseBlock] = None

    def connect_first(self, block: BaseBlock) -> None:
        """Connect the first output (for container)."""
        self._first_output = block

    def connect_second(self, block: BaseBlock) -> None:
        """Connect the second output (for children)."""
        self._second_output = block

    def take(self, agent: BaseAgent) -> None:
        """Split container into itself and its children."""
        agent._enter_block(self)
        if self.on_enter is not None:
            self.on_enter(agent)

        if not hasattr(agent, 'children_agents') or not isinstance(agent.children_agents, list):
            raise RuntimeError(f"Agent {id(agent)} has no children_agents list. Not a valid container.")

        if self._second_output is None:
            raise RuntimeError("SplitBlock second output is not connected.")
        if self._first_output is None:
            raise RuntimeError("SplitBlock first output is not connected.")

        # Eject children to second output
        for child in agent.children_agents:
            if not hasattr(child, 'parent_agents'):
                child.parent_agents = []
            if agent not in child.parent_agents:
                child.parent_agents.append(agent)
            self._second_output.take(child)

        # Eject container (now empty) to first output
        agent.children_agents.clear()
        self._first_output.take(agent)
