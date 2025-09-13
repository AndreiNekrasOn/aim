# core/block.py

from .agent import BaseAgent
from typing import Optional, List
from abc import ABC, abstractmethod

class BaseBlock(ABC):
    """
    Abstract base class for all blocks.
    Blocks control agent flow: they accept agents, may hold them (multi-tick),
    and route them to connected blocks based on internal logic or agent state.
    """

    def __init__(self):
        self._agents: List[BaseAgent] = []  # Agents currently "in" this block
        self.output_connections: List[Optional['BaseBlock']] = []  # e.g., [next_block]

    @abstractmethod
    def take(self, agent: 'BaseAgent') -> bool:
        """
        Accept an agent into this block.
        Must be overridden by subclasses.
        Typically:
          - Adds agent to internal list/queue
          - May trigger immediate processing or hold for multiple ticks
        """
        pass

    def connect(self, *blocks: 'BaseBlock') -> None:
        """
        Connect this block to one or more output blocks.
        Default: stores in self.output_connections[0], [1], etc.
        Subclasses may override or add semantic meaning (e.g., IfBlock.connect_first/second).
        """
        self.output_connections.extend(blocks)

    def _tick(self) -> None:
        """
        Internal method called by simulator each tick.
        Subclasses may override to implement multi-tick behavior (e.g., ConveyBlock).
        Default: do nothing — assume instant processing.
        """
        pass

    def _eject_all(self) -> List['BaseAgent']:
        """
        Internal: eject all agents from this block (e.g., at sim end or for testing).
        Returns list of agents removed.
        """
        agents = self._agents[:]
        self._agents.clear()
        return agents

    @property
    def agents(self) -> List['BaseAgent']:
        """Read-only list of agents currently in this block."""
        return self._agents[:]
