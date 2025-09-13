# core/simulator.py

from typing import List, Dict, Callable, Any, Set
from collections import defaultdict
import random

from .agent import BaseAgent
from .block import BaseBlock


class Simulator:
    """
    Central simulation controller.
    Manages ticks, agents, blocks, agent-emitted events, and scheduled timed events.
    """

    def __init__(self, max_ticks: int = 1000, random_seed: int = 42):
        self.max_ticks = max_ticks
        self.current_tick = 0
        self.random_seed = random_seed
        random.seed(self.random_seed)  # For event ordering

        self.blocks: List[BaseBlock] = []
        self.agents: List[BaseAgent] = []

        # --- Agent Event System ---
        # Subscription: event string -> set of agents
        self._event_subscriptions: Dict[str, Set[BaseAgent]] = defaultdict(set)
        # Pending delivery: agent -> list of events (to be delivered next tick)
        self._pending_events: Dict[BaseAgent, List[str]] = defaultdict(list)
        # Events emitted this tick (collected at end of tick)
        self._events_this_tick: List[str] = []

        # --- Scheduled Timed Events ---
        # Format: { tick: [ (callback, is_recurring, interval) ] }
        self._scheduled_events: Dict[int, List[Any]] = defaultdict(list)
        # Flag to prevent event callbacks from scheduling new events during execution
        self._event_scheduling_locked = False

    def add_block(self, block: BaseBlock) -> None:
        """Register a block and inject simulator reference."""
        block._simulator = self
        self.blocks.append(block)

    def subscribe(self, agent: BaseAgent, event: str) -> None:
        """Subscribe agent to receive an event (exact match)."""
        self._event_subscriptions[event].add(agent)

    def schedule_event(
        self,
        callback: Callable[[int], None],
        delay_ticks: int = 0,
        recurring: bool = False
    ) -> None:
        """
        Schedule a callback to be executed at `current_tick + delay_ticks`.
        Callback receives `current_tick` as argument.
        If `recurring=True`, event will auto-reschedule itself every `delay_ticks`.
        Events cannot schedule new events during execution (runtime error if attempted).
        """
        if self._event_scheduling_locked:
            raise RuntimeError("Cannot schedule new events during event execution.")

        target_tick = self.current_tick + delay_ticks
        self._scheduled_events[target_tick].append((callback, recurring, delay_ticks))

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
        1. Execute scheduled events for this tick (in randomized order).
        2. Deliver pending agent-emitted events (from last tick).
        3. Advance all blocks (call ._tick()).
        4. Collect new agent-emitted events (for delivery next tick).
        """
        self._process_scheduled_events()
        self._deliver_pending_events()
        for block in self.blocks:
            block._tick()
        self._collect_emitted_events()

    def _process_scheduled_events(self) -> None:
        """Execute all callbacks scheduled for current_tick in randomized order."""
        events = self._scheduled_events.pop(self.current_tick, [])
        if not events:
            return

        # Shuffle order for this tick (reproducible via seed)
        shuffled_events = events[:]
        random.shuffle(shuffled_events)

        # Lock event scheduling during execution
        self._event_scheduling_locked = True
        reschedule_queue = []  # (callback, interval) tuples to reschedule AFTER unlock
        try:
            for callback, recurring, interval in shuffled_events:
                callback(self.current_tick)
                if recurring:
                    # Queue for rescheduling — do NOT schedule while locked
                    reschedule_queue.append((callback, interval))
        finally:
            self._event_scheduling_locked = False

        # Now safely reschedule recurring events
        for callback, interval in reschedule_queue:
            self.schedule_event(callback, interval, recurring=True)


    def _deliver_pending_events(self) -> None:
        """Deliver staged events to agents and trigger on_event."""
        for agent, events in self._pending_events.items():
            for event in events:
                agent._receive_event(event)
            agent._process_pending_events()
        self._pending_events.clear()

    def _collect_emitted_events(self) -> None:
        """Gather all events emitted this tick and stage for next tick delivery."""
        emitted_events = []

        for agent in self.agents:
            emitted = agent._collect_emitted_events()
            emitted_events.extend(emitted)

        for block in self.blocks:
            for agent in block.agents:
                emitted = agent._collect_emitted_events()
                emitted_events.extend(emitted)

        for event in emitted_events:
            for agent in self._event_subscriptions.get(event, set()):
                self._pending_events[agent].append(event)

    def stop(self) -> None:
        """Stop simulation at end of current tick."""
        self.max_ticks = 0

    def add_agent(self, agent: BaseAgent) -> None:
        """Manually add an agent to simulation."""
        self.agents.append(agent)
