# core/simulator.py

from typing import List, Dict, Set, Type
from collections import defaultdict
from .agent import BaseAgent
from .block import BaseBlock

class Simulator:
    """
    Central simulation controller.
    Manages ticks, agents, blocks, and event delivery.
    Events are delivered next tick to agents that subscribe to exact event string.
    """

    def __init__(self, max_ticks: int = 1000):
        self.max_ticks = max_ticks
        self.current_tick = 0

        self.blocks: List[BaseBlock] = []
        self.agents: List[BaseAgent] = []  # Global registry (optional, for inspection)

        # Event system: map event string → set of agents subscribed to it
        self._event_subscriptions: Dict[str, Set[BaseAgent]] = defaultdict(set)
        self._pending_events: Dict[BaseAgent, List[str]] = defaultdict(list)  # agent → [events to deliver next tick]
        self._events_this_tick: List[str] = []  # events emitted during current tick

    def add_block(self, block: BaseBlock) -> None:
        """Register a block to be included in simulation ticks."""
        self.blocks.append(block)

    def subscribe(self, agent: BaseAgent, event: str) -> None:
        """
        Subscribe agent to receive an event (exact match).
        Called by agent or user during setup.
        Example: agent subscribes to "order_complete"
        """
        self._event_subscriptions[event].add(agent)

    def run(self) -> None:
        """Run simulation until max_ticks reached or manually stopped."""
        while self.current_tick < self.max_ticks:
            self.tick()
            self.current_tick += 1
            if self.max_ticks == 0:  # manual stop
                break

    def tick(self) -> None:
        """
        Execute one simulation tick in this order:
        1. Deliver pending events (from last tick) to agents.
        2. Let each block perform its tick logic (e.g., Source spawns, Convey moves).
        3. Collect all events emitted during this tick.
        4. Stage them for delivery next tick (filtered by subscription).
        """
        # 1. Deliver events from last tick
        self._deliver_pending_events()

        # 2. Advance all blocks
        for block in self.blocks:
            block._tick()

        # 3. Collect events emitted during this tick (via agent.emit_event)
        self._collect_emitted_events()

    def _deliver_pending_events(self) -> None:
        """Deliver staged events to agents and trigger on_event."""
        for agent, events in self._pending_events.items():
            for event in events:
                agent._receive_event(event)
            agent._process_pending_events()  # calls agent.on_event for each
        self._pending_events.clear()

    def _collect_emitted_events(self) -> None:
        """Gather all events emitted this tick and stage for next tick delivery."""
        emitted_events = []

        # Collect from all agents
        for agent in self.agents:
            emitted = agent._collect_emitted_events()
            emitted_events.extend(emitted)

        # Also check agents inside blocks (in case new agents spawned and emitted)
        for block in self.blocks:
            for agent in block.agents:
                emitted = agent._collect_emitted_events()
                emitted_events.extend(emitted)

        # Stage for next tick: map event → subscribed agents
        for event in emitted_events:
            for agent in self._event_subscriptions.get(event, set()):
                self._pending_events[agent].append(event)

    def stop(self) -> None:
        """Stop simulation at end of current tick."""
        self.max_ticks = 0

    def add_agent(self, agent: BaseAgent) -> None:
        """
        Manually add an agent to simulation (e.g., pre-seeded agents).
        Usually agents enter via SourceBlock, but this allows direct injection.
        """
        self.agents.append(agent)
