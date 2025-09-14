# core/agent.py

from typing import Optional, List

class BaseAgent:
    """
    Passive data container representing an agent in the simulation.
    Reacts only to entering a block or receiving an event.
    Agents influence simulation only by:
      - Changing internal state (e.g., self.is_happy = True)
      - Emitting events (via self.emit_event(...))
    """

    def __init__(self):
        self._current_block = None
        self._pending_events: List[str] = []
        self.position = None
        self.velocity = None
        # User-defined state goes here — no schema enforced.
        # Example: self.is_happy = False, self.energy = 100, etc.

    def on_enter_block(self, block) -> None:
        """
        Called when agent enters a new block.
        Override to react to block entry.
        """
        pass

    def on_event(self, event: str) -> None:
        """
        Called (next tick) when agent receives an event it subscribed to.
        Override to react to events.
        Event delivery is delayed by one tick to prevent recursion.
        """
        pass

    def emit_event(self, event: str) -> None:
        """
        Emit an event to be delivered to all agents next tick
        (filtered by exact string match against their subscriptions).
        Called during on_enter_block or on_event.
        """
        # Simulator will collect this during tick and dispatch next tick.
        # We just stage it here.
        if not hasattr(self, '_emitted_events_this_tick'):
            self._emitted_events_this_tick = []
        self._emitted_events_this_tick.append(event)

    @property
    def current_block(self):
        """Read-only accessor to current block (set by simulator)."""
        return self._current_block

    def _enter_block(self, block) -> None:
        """Internal method called by simulator to update block and trigger hook."""
        self._current_block = block
        self.on_enter_block(block)

    def _receive_event(self, event: str) -> None:
        """Internal method called by simulator to deliver event next tick."""
        self._pending_events.append(event)

    def _process_pending_events(self) -> None:
        """Called by simulator at start of tick to flush and handle events."""
        for event in self._pending_events:
            self.on_event(event)
        self._pending_events.clear()

    def _collect_emitted_events(self) -> List[str]:
        """Called by simulator at end of tick to gather emitted events."""
        emitted = getattr(self, '_emitted_events_this_tick', [])
        self._emitted_events_this_tick = []
        return emitted
