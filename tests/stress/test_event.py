from aim.core import Simulator

def test_event_stress():
    sim = Simulator(max_ticks=100)

    counter = 0
    def event_callback(tick):
        nonlocal counter
        counter += 1

    for i in range(1000):
        sim.schedule_event(event_callback, delay_ticks=0, recurring=True)

    sim.run()
    assert counter >= 1000 * 100  # 1000 events * 100 ticks
