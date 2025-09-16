# blocks/sink.py

from ..core.block import BaseBlock
from ..core.agent import BaseAgent
from ..core.simulator import Simulator

class SinkBlock(BaseBlock):
    """
    Terminal block that absorbs and holds agents indefinitely.
    Useful for counting, logging, or ending agent journeys.
    """

    def __init__(self,
            simulator: Simulator):
        super().__init__(simulator)
        self.simulator = simulator

    def take(self, agent: BaseAgent) -> None:
        """
        Accept and hold agent forever (or until simulation ends).
        Agents are stored internally and not passed on.
        """
        agent._enter_block(self)
        self._agents.append(agent)
        if self.on_enter is not None:
            self.on_enter(agent)
        try:
            self.simulator.remove_agent(agent)
        except Exception:
            pass

    def _tick(self) -> None:
        """
        SinkBlock does nothing on tick — agents just sit here.
        Override if you want to add logging or auto-eject after N ticks.
        """
        pass

    @property
    def count(self) -> int:
        """Convenience: return number of agents absorbed."""
        return len(self._agents)
