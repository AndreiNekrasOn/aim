from aim import BaseAgent, SourceBlock, IfBlock, SinkBlock, Simulator

class HappyAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.is_happy = False  # Default: not happy

    def on_enter_block(self, block):
        # Become happy if entering the source block
        if isinstance(block, SourceBlock):
            self.is_happy = True
            print(f"Agent became happy in {block.__class__.__name__}")

    def on_event(self, event):
        pass  # Not using events in this example


# --- Build simulation ---

# Create blocks
source = SourceBlock(agent_class=HappyAgent, spawn_rate=1)
happy_sink = SinkBlock()
grumpy_sink = SinkBlock()

# Router: send happy agents to happy_sink, others to grumpy_sink
router = IfBlock(condition=lambda agent: agent.is_happy)
router.connect_first(happy_sink)    # True branch
router.connect_second(grumpy_sink)  # False branch
source.connect(router)

# Create and run simulator
sim = Simulator(max_ticks=5)
sim.add_block(source)
sim.add_block(router)
sim.add_block(happy_sink)
sim.add_block(grumpy_sink)

sim.run()

# --- Results ---
print(f"\nSimulation finished.")
print(f"Happy agents: {happy_sink.count}")
print(f"Grumpy agents: {grumpy_sink.count}")
