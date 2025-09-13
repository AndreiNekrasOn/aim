# blocks/source.py

from typing import Type, Optional, List, Callable

from ..core.block import BaseBlock
from ..core.agent import BaseAgent
from ..core.simulator import Simulator

class SourceBlock(BaseBlock):
    """
    Spawns new agents into the simulation each tick.
    Connects to one output block (e.g., a conveyor or router).
    """

    def __init__(
        self,
        simulator: Simulator,
        agent_class: Type[BaseAgent] = BaseAgent,
        spawn_schedule: Callable[[int], int] = lambda tick: 1
    ):
        """
        :param agent_class: Class to instantiate for each spawned agent.
        :param spawn_schedule: Function that takes current_tick and returns number of agents to spawn this tick.
                               Default: spawns 1 agent per tick.
        """
        super().__init__(simulator)
        self.agent_class = agent_class
        self.spawn_schedule = spawn_schedule

    def take(self, agent: BaseAgent) -> None:
        # SourceBlock doesn't accept incoming agents — ignore.
        pass

    def _tick(self) -> None:
        if not self.output_connections:
            return

        target_block = self.output_connections[0]
        if target_block is None:
            return

        # Ask schedule how many agents to spawn THIS tick
        count = self.spawn_schedule(self._simulator.current_tick)  # ← We need simulator reference

        for _ in range(count):
            agent = self.agent_class()
            agent._enter_block(self)
            self._eject(agent)

    @staticmethod
    def every_n_ticks(n: int, count: int = 1) -> Callable[[int], int]:
        return lambda tick: count if tick % n == 0 else 0

    @staticmethod
    def random_burst(p: float, burst_size: int) -> Callable[[int], int]:
        import random
        return lambda tick: burst_size if random.random() < p else 0
