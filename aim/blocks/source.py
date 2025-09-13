# blocks/source.py

from typing import Type, Optional, List
from ..core.block import BaseBlock
from ..core.agent import BaseAgent

class SourceBlock(BaseBlock):
    """
    Spawns new agents into the simulation each tick.
    Connects to one output block (e.g., a conveyor or router).
    """

    def __init__(self, agent_class: Type[BaseAgent] = BaseAgent, spawn_rate: int = 1):
        """
        :param agent_class: Class to instantiate for each spawned agent.
        :param spawn_rate: Number of agents to spawn per tick.
        """
        super().__init__()
        self.agent_class = agent_class
        self.spawn_rate = spawn_rate

    def take(self, agent: BaseAgent) -> None:
        """
        SourceBlock doesn't accept incoming agents — it only spawns new ones.
        You may choose to ignore or raise if called.
        """
        # Optional: warn or raise if someone tries to push agent into Source
        # For now, silently ignore.
        pass

    def _tick(self) -> None:
        """
        Called by simulator each tick.
        Spawns `spawn_rate` new agents and pushes them to the first connected block.
        """
        if not self.output_connections:
            return  # nowhere to send agents

        target_block = self.output_connections[0]
        if target_block is None:
            return

        for _ in range(self.spawn_rate):
            agent = self.agent_class()
            agent._enter_block(self)
            target_block.take(agent)
