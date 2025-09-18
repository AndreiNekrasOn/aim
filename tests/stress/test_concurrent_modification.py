from aim.core import Simulator
from aim.blocks import SourceBlock, SinkBlock, SwitchBlock

def test_concurrent_modification():
    sim = Simulator(max_ticks=100)
    source = SourceBlock(sim, spawn_schedule=lambda t: 10 if t < 10 else 0)
    switch = SwitchBlock(sim, key_func=lambda a: getattr(a, 'key', 0))
    sink0 = SinkBlock(sim)
    sink1 = SinkBlock(sim)

    switch.connect(0, sink0)
    switch.connect(1, sink1)
    source.connect(switch)

    def modify_connections():
        # Simulate dynamic reconfiguration
        switch._output_map[2] = sink0  # Add new route

    sim.schedule_event(lambda t: modify_connections(), delay_ticks=5, recurring=False)
    sim.run()
    assert sink0.count + sink1.count >= 90  # Most agents routed
