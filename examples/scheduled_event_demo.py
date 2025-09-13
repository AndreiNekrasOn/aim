# examples/scheduled_event_demo.py

from aim import BaseAgent, Simulator

def log_tick(tick: int):
    print(f"Event fired at tick {tick}")


sim = Simulator(max_ticks=5, random_seed=123)

sim.schedule_event(log_tick, delay_ticks=2, recurring=True)
sim.schedule_event(log_tick, delay_ticks=1, recurring=True)

sim.run()
