import time
import psutil
import os

from aim.core import Simulator, BaseAgent
from aim.blocks import SourceBlock, SinkBlock


def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss

def test_long_running():
    sim = Simulator(max_ticks=1_000_000)
    source = SourceBlock(sim, spawn_schedule=lambda t: 1 if t % 1000 == 0 else 0)
    sink = SinkBlock(sim)
    source.connect(sink)
    start_mem = get_memory_usage()
    sim.run()
    end_mem = get_memory_usage()
    assert end_mem - start_mem < 10 * 1024 * 1024  # < 10MB growth
    assert sink.count == 1000

if __name__ == '__main__':
    test_long_running()
