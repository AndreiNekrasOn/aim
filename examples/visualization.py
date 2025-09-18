import sys
import argparse

from aim.blocks.source import SourceBlock
from aim.blocks.sink import SinkBlock
from aim.core.agent import BaseAgent
from aim.core.simulator import Simulator
from aim.spaces.manufacturing.conveyor_space import ConveyorSpace
from aim.entities.manufacturing.conveyor import Conveyor
from aim.visualization.console_viewer import ConsoleViewer
from aim.blocks.manufacturing.conveyor_block import ConveyorBlock
from aim.blocks import DelayBlock


def create_viewer(viz_type: str, simulator):
    """Factory function to create viewer based on type."""
    if viz_type == "console":
        from aim.visualization.console_viewer import ConsoleViewer
        return ConsoleViewer(simulator)
    elif viz_type == "matplotlib":
        try:
            from aim.visualization.matplotlib_viewer import Matplotlib2DViewer
            return Matplotlib2DViewer(simulator)
        except ImportError as e:
            print(f"[ERROR] matplotlib viewer not available: {e}", file=sys.stderr)
            print("[INFO] Falling back to console viewer.", file=sys.stderr)
            from aim.visualization.console_viewer import ConsoleViewer
            return ConsoleViewer(simulator)
    else:
        print(f"[WARNING] Unknown viz type '{viz_type}', using console.", file=sys.stderr)
        from aim.visualization.console_viewer import ConsoleViewer
        return ConsoleViewer(simulator)

NAME = 1
class Box(BaseAgent):
    def __init__(self):
        global NAME
        super().__init__()
        self.length = 0.0  # 2m long
        self.name = NAME
        NAME += 1

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run conveyor simulation with optional visualization.')
    parser.add_argument('--viz', type=str, default='console',
                        choices=['console', 'matplotlib'],
                        help='Visualization backend: "console" or "matplotlib" (default: console)')

    args = parser.parse_args()

    space = ConveyorSpace()
    sim = Simulator(max_ticks=30, spaces={"main_line": space})

    # Create viewer based on argument
    viewer = create_viewer(args.viz, sim)
    sim.viewer = viewer

    # Build simulation
    source = SourceBlock(sim, agent_class=Box)
    A = Conveyor([(0.0, 0.0, 0.0), (0.0, 10.0, 0.0)], speed=1, name='A')
    B = Conveyor([(0.0, 10.0, 0.0), (10.0, 30.0, 0.0)], speed=2, name='B')
    A.connections.append(B)
    space.register_entity(A)
    space.register_entity(B)
    conv = ConveyorBlock(sim, start_entity=A, end_entity=B, space_name="main_line")
    delay = DelayBlock(sim, delay_ticks=5)
    sink = SinkBlock(sim)

    source.connect(conv)
    conv.connect(delay)
    delay.connect(sink)

    # Run
    sim.run()

    # If matplotlib, show plot after run
    if args.viz == "matplotlib":
        try:
            viewer.show_final()
        except Exception as e:
            print(f"[ERROR] Failed to show final plot: {e}", file=sys.stderr)
