from aim.core.agent import BaseAgent
from aim.entities.manufacturing.conveyor import Conveyor

class ConsoleViewer:
    """Simple text-based viewer for debugging."""

    def __init__(self, simulator):
        self.simulator = simulator

    def render_tick(self, tick: int):
        print(f"\n=== TICK {tick} ===")
        for agent in self.simulator.agents:
            state = agent.space_state
            entity = state.get("entity")
            progress = state.get("progress_on_entity", 0.0)
            path = state.get("path", [])
            if state and "entity" in state:
                path_names = [getattr(e, 'name', 'unnamed') for e in state.get("path", [])]
                print(f"Agent {agent.name}: on {getattr(entity, 'name', 'unknown')}, "
                      f"progress={progress:.2f}, path=[{', '.join(path_names)}]")
