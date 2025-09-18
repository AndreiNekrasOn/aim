from typing import Any, Callable, Hashable, Dict, Optional
from aim.core.block import BaseBlock
from aim.core.agent import BaseAgent
from aim.core.simulator import Simulator

class SwitchBlock(BaseBlock):
    """
    Routes agents to different output blocks based on a key function.
    Like a switch-case statement: key -> output connection.
    Keys can be any hashable type (str, int, Conveyor, etc.).
    """

    def __init__(
        self,
        simulator: Simulator,
        key_func: Callable[[BaseAgent], Hashable]
    ):
        """
        Initialize SwitchBlock.
        :param simulator: Simulator instance.
        :param key_func: Function that takes agent and returns a hashable key.
        """
        super().__init__(simulator)
        self.key_func = key_func
        self._output_map: Dict[Hashable, BaseBlock] = {}

    def connect(self, key: Hashable, block: BaseBlock) -> None:
        """
        Connect an output block to a key.
        :param key: Hashable key (e.g., str, int, Conveyor).
        :param block: Target block for this key.
        """
        if not isinstance(key, Hashable):
            raise TypeError(f"Key {key} is not hashable.")
        self._output_map[key] = block

    def take(self, agent: BaseAgent) -> None:
        """
        Route agent to output block based on key_func(agent).
        Raises RuntimeError if no output is connected for the key.
        """
        agent._enter_block(self)
        if self.on_enter is not None:
            self.on_enter(agent)

        try:
            key = self.key_func(agent)
        except Exception as e:
            raise RuntimeError(f"SwitchBlock: key_func failed for agent {id(agent)}: {e}")

        if key not in self._output_map:
            raise RuntimeError(f"SwitchBlock: no output connected for key: {key}")

        target_block = self._output_map[key]
        if target_block is None:
            raise RuntimeError(f"SwitchBlock: output for key {key} is None")

        # Call target block directly — bypass _eject
        target_block.take(agent)
