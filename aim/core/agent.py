# core/agent.py

from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .block import BaseBlock

class BaseAgent:
    """
    Base class for all agents in the simulation.
    Agents are passive — react to events and block entry.
    Spatial state is managed by SpaceManager — stored in .space_state.
    """

    def __init__(self):
        # Spatial dimensions — default to 0.0 for non-spatial agents
        self.width: float = 0.0
        self.length: float = 0.0

        # Space-specific state — managed by SpaceManager
        self.space_state: Dict[str, Any] = {}

        # Event system — internal staging
        self._pending_events: List[str] = []
        if not hasattr(self, '_emitted_events_this_tick'):
            self._emitted_events_this_tick = []

        # Current block — set by simulator
        self._current_block: Optional['BaseBlock'] = None

    def on_enter_block(self, block: 'BaseBlock') -> None:
        """Called when agent enters a block. Override to react."""
        pass

    def on_event(self, event: str) -> None:
        """Called when agent receives an event. Override to react."""
        pass

    def emit_event(self, event: str) -> None:
        """Emit an event to be delivered next tick."""
        self._emitted_events_this_tick.append(event)

    @property
    def current_block(self) -> Optional['BaseBlock']:
        return self._current_block

    def _enter_block(self, block: 'BaseBlock') -> None:
        """Internal: called by simulator to update block and trigger hook."""
        self._current_block = block
        self.on_enter_block(block)

    def _receive_event(self, event: str) -> None:
        """Internal: called by simulator to deliver event."""
        self._pending_events.append(event)

    def _process_pending_events(self) -> None:
        """Internal: called by simulator to flush and handle events."""
        for event in self._pending_events:
            self.on_event(event)
        self._pending_events.clear()

    def _collect_emitted_events(self) -> List[str]:
        """Internal: called by simulator to gather emitted events."""
        emitted = self._emitted_events_this_tick[:]
        self._emitted_events_this_tick.clear()
        return emitted
