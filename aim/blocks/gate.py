from typing import List
from ..core.block import BaseBlock
from ..core.agent import BaseAgent
from ..core.simulator import Simulator
from . import QueueBlock

class GateBlock(BaseBlock):
    def __init__(
        self,
        simulator: Simulator,
        initial_state: str = "closed",
        release_mode: str = "one"  # "one" or "all"
    ):
        super().__init__(simulator)
        self._state = initial_state
        self._release_mode = release_mode
        self._waiting_agents: List[BaseAgent] = []

        if initial_state not in ["open", "closed"]:
            raise ValueError("initial_state must be 'open' or 'closed'")
        if release_mode not in ["one", "all"]:
            raise ValueError("release_mode must be 'one' or 'all'")

    def take(self, agent: BaseAgent) -> None:
        # Enforce: previous block must be QueueBlock
        if not isinstance(agent.current_block, QueueBlock):
            raise RuntimeError(
                f"GateBlock {id(self)} only accepts agents from QueueBlock. "
                f"Agent {id(agent)} came from {type(agent.current_block).__name__}."
            )

        agent._enter_block(self)
        if self.on_enter is not None:
            self.on_enter(agent)

        self._waiting_agents.append(agent)

    def _tick(self) -> None:
        if self._state == "open":
            if self._release_mode == "one" and self._waiting_agents:
                agent = self._waiting_agents.pop(0)
                self._eject(agent)
            elif self._release_mode == "all" and self._waiting_agents:
                agents = self._waiting_agents[:]
                self._waiting_agents.clear()
                for agent in agents:
                    self._eject(agent)

    def toggle(self) -> None:
        """Toggle gate state: open ↔ closed."""
        self._state = "closed" if self._state == "open" else "open"

    def state(self) -> str:
        """Return current state: 'open' or 'closed'."""
        return self._state

    def open(self) -> None:
        """Open gate."""
        self._state = "open"

    def close(self) -> None:
        """Close gate."""
        self._state = "closed"

    @property
    def size(self) -> int:
        """Number of agents waiting at gate."""
        return len(self._waiting_agents)
