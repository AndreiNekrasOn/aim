# examples/callback_event_demo.py

"""
CALLBACK + EVENT SYNCHRONIZATION DEMO

Models a factory where:
- Agents (workers) flow: Source → Delay → Sink.
- Every block fires on_enter/on_exit callbacks (logging).
- Every agent fires on_enter_block (logging).
- When FIRST agent reaches SinkBlock, it emits "factory_alert" event.
- ALL agents (wherever they are) receive event next tick → set self.alerted = True.

Tests:
- Block callbacks (on_enter, on_exit).
- Agent callbacks (on_enter_block).
- Global event delivery (exact match, next tick).
- State mutation via events.
"""

from aim import BaseAgent, Simulator
from aim.blocks.source import SourceBlock
from aim.blocks.delay import DelayBlock
from aim.blocks.sink import SinkBlock

class WorkerAgent(BaseAgent):
    """Worker agent that reacts to factory_alert event."""
    def __init__(self):
        super().__init__()
        self.alerted = False
        self.agent_id = id(self)

    def on_enter_block(self, block):
        print(f"  [AGENT {self.agent_id}] Entered {block.__class__.__name__}")

    def on_event(self, event):
        if event == "factory_alert":
            self.alerted = True
            print(f"  [AGENT {self.agent_id}] ALERT RECEIVED — state changed to alerted=True")


def main():
    sim = Simulator(max_ticks=20)

    # Blocks
    source = SourceBlock(
        simulator=sim,
        agent_class=WorkerAgent,
        spawn_schedule=lambda tick: 1 if tick in [1, 3, 5] else 0  # spawn at tick 1,3,5
    )

    delay = DelayBlock(simulator=sim, delay_ticks=2)

    sink = SinkBlock(simulator=sim)

    # Block callbacks
    def block_on_enter(agent):
        print(f"[BLOCK] Agent {agent.agent_id} ENTERED {agent.current_block.__class__.__name__}")

    def block_on_exit(agent):
        print(f"[BLOCK] Agent {agent.agent_id} EXITED {agent.current_block.__class__.__name__}")

    source.on_enter = block_on_enter
    source.on_exit = block_on_exit
    delay.on_enter = block_on_enter
    delay.on_exit = block_on_exit
    sink.on_enter = block_on_enter
    # sink has no on_exit — terminal

    # Wire
    source.connect(delay)
    delay.connect(sink)

    # Track first agent to reach sink
    first_alert_emitted = False

    def sink_on_enter(agent):
        nonlocal first_alert_emitted
        print(f"[BLOCK] Agent {agent.agent_id} ENTERED SinkBlock")
        if not first_alert_emitted:
            print(f"  ⚠️  FIRST AGENT REACHED SINK — EMITTING 'factory_alert'")
            agent.emit_event("factory_alert")
            first_alert_emitted = True

    sink.on_enter = sink_on_enter

    # Subscribe all agents to "factory_alert"
    def subscribe_agent(agent):
        sim.subscribe(agent, "factory_alert")

    # Monkey-patch SourceBlock.take to auto-subscribe (just for demo)
    original_take = source.take
    def take_and_subscribe(agent):
        subscribe_agent(agent)
        original_take(agent)
    source.take = take_and_subscribe

    # Run
    print("🚀 STARTING CALLBACK + EVENT SYNCHRONIZATION DEMO\n")
    sim.run()

    # Results
    print("\n📊 FINAL AGENT STATES:")
    all_agents = []
    for block in [source, delay, sink]:
        if hasattr(block, '_agents'):
            all_agents.extend(block._agents)
    # Also check agents in simulator (if any)
    all_agents.extend(sim.agents)

    for agent in all_agents:
        print(f"Agent {agent.agent_id}: alerted={agent.alerted}")

    print("\n✅ DEMO COMPLETED")


if __name__ == "__main__":
    main()
