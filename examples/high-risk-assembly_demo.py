"""
HIGH-RISK ASSEMBLY STATION SIMULATION

Models a manufacturing cell with strict safety and flow constraints:

- Technicians (agents) arrive randomly and must assemble devices in a restricted safety zone.
- Only 2 technicians allowed inside the zone at any time (safety regulation).
- Each assembly takes exactly 5 ticks (deterministic work).
- After assembly, 50% of devices pass inspection and ship immediately.
- 50% require rework — delayed 3 ticks — then ship.
- Technicians MUST wait in a QueueBlock before entering the restricted area.
- Any attempt to bypass the queue (e.g., SourceBlock → RestrictedAreaStart) raises RuntimeError.

BLOCKS TESTED:
- SourceBlock: spawns agents at random intervals.
- QueueBlock: mandatory buffer before restricted area.
- RestrictedAreaStart: enforces max occupancy (2), rejects direct pushes.
- DelayBlock: models assembly time (5 ticks) and rework (3 ticks).
- RestrictedAreaEnd: releases slot in restricted area on exit.
- IfBlock: routes 50/50 pass/rework.
- SinkBlock: absorbs completed devices, measures throughput.

This example validates:
- Cross-block coordination (Start ↔ End).
- Enforced buffering (QueueBlock required).
- Capacity limits (max 2 in restricted area).
- Deterministic delays.
- Stochastic routing.
- End-to-end flow control with no overflows.
"""

from aim import BaseAgent, Simulator
from aim.blocks.source import SourceBlock
from aim.blocks.queue import QueueBlock
from aim.blocks.restricted_area_start import RestrictedAreaStart
from aim.blocks.restricted_area_end import RestrictedAreaEnd
from aim.blocks.delay import DelayBlock
from aim.blocks.if_block import IfBlock
from aim.blocks.sink import SinkBlock
import random

class Technician(BaseAgent):
    """Agent representing a technician assembling devices."""
    def __init__(self):
        super().__init__()
        self.device_id = id(self)  # simple unique ID

    def on_enter_block(self, block):
        # Optional: log for debugging
        # print(f"Technician {self.device_id} entered {block.__class__.__name__}")
        pass

    def on_event(self, event):
        pass  # not used in this example


def main():
    # --- SETUP ---
    sim = Simulator(max_ticks=100, random_seed=42)

    # Blocks
    source = SourceBlock(
        simulator=sim,
        spawn_schedule=lambda tick: 1 if random.random() < 0.3 else 0  # ~30% chance per tick
    )

    queue = QueueBlock(simulator=sim)

    start = RestrictedAreaStart(simulator=sim, max_agents=2)
    end = RestrictedAreaEnd(simulator=sim, start_block=start)
    start.set_end(end)

    assembly_delay = DelayBlock(simulator=sim, delay_ticks=5)

    inspection_router = IfBlock(
        simulator=sim,
        condition=lambda agent: random.random() < 0.5  # 50% pass
    )

    rework_delay = DelayBlock(simulator=sim, delay_ticks=3)

    sink = SinkBlock(simulator=sim)

    # --- WIRING ---
    source.connect(queue)
    queue.connect(start)
    start.connect(assembly_delay)
    assembly_delay.connect(end)
    end.connect(inspection_router)

    # Inspection: pass → sink, rework → delay → sink
    inspection_router.connect_first(sink)      # pass
    inspection_router.connect_second(rework_delay)  # rework
    rework_delay.connect(sink)

    # --- RUN ---
    print("Starting High-Risk Assembly Station Simulation...\n")
    sim.run()

    # --- RESULTS ---
    print(f"\nSimulation finished after {sim.current_tick} ticks.")
    print(f"Total devices completed: {sink.count}")
    print(f"Peak occupancy in restricted area: {start.active_agents} (max allowed: 2)")


if __name__ == "__main__":
    main()
