# examples/gate_feedback_demo.py

"""
GATE FEEDBACK CONTROL DEMO

Flow: Source -> Queue -> Gate -> Delay -> Sink

- Gate starts CLOSED.
- Every 5 ticks, a scheduled event TOGGLES the gate.
- When a SINGLE agent passes through the gate, it TOGGLES the gate again.

This creates a feedback loop:
  - Gate opens (event) -> agent passes -> gate closes (agent action).
  - Gate closes (event) -> no agent passes -> gate stays closed until next event.
"""

from aim import BaseAgent, Simulator
from aim.blocks.source import SourceBlock
from aim.blocks.queue import QueueBlock
from aim.blocks.gate import GateBlock
from aim.blocks.delay import DelayBlock
from aim.blocks.sink import SinkBlock

class ItemAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.agent_id = id(self)

    def on_enter_block(self, block):
        pass

def main():
    sim = Simulator(max_ticks=30)

    source = SourceBlock(
        simulator=sim,
        agent_class=ItemAgent,
        spawn_schedule=lambda tick: 1 if tick % 3 == 0 else 0
    )

    queue = QueueBlock(simulator=sim)
    gate = GateBlock(simulator=sim, initial_state="closed", release_mode="one")
    delay = DelayBlock(simulator=sim, delay_ticks=2)
    sink = SinkBlock(simulator=sim)

    source.connect(queue)
    queue.connect(gate)
    gate.connect(delay)
    delay.connect(sink)

    def toggle_gate_event(tick):
        print(f"[TICK {tick}] Scheduled event: TOGGLING gate")
        gate.toggle()

    sim.schedule_event(callback=toggle_gate_event, delay_ticks=5, recurring=True)

    def on_agent_exit_gate(agent):
        print(f"[AGENT {agent.agent_id}] passed gate -> TOGGLING gate")
        gate.toggle()

    gate.on_exit = on_agent_exit_gate

    print("STARTING GATE FEEDBACK DEMO\n")
    sim.run()

    assert sink.count == 5
    assert gate.state() == "closed"
    print(f"\nTOTAL AGENTS PROCESSED: {sink.count}")
    print(f"FINAL GATE STATE: {gate.state()}")

def test_gate():
    main()

if __name__ == '__main__':
    main()

