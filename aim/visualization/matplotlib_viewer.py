import matplotlib.pyplot as plt
import sys
from aim.entities.manufacturing.conveyor import Conveyor

class Matplotlib2DViewer:
    def __init__(self, simulator):
        self.simulator = simulator
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        self.ax.set_title("Conveyor System")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.grid(True)
        plt.ion()

        # Placeholder for agent scatter
        self.agent_scatter = None
        self.agent_annotations = []

        # Flag to draw conveyors once
        self._conveyors_drawn = False

    def _draw_conveyors(self):
        """Draw all conveyors from space — called once, lazily."""
        if self._conveyors_drawn:
            return

        print("[DEBUG] Drawing conveyors (lazy init)...")
        space = getattr(self.simulator, 'space', None)
        if space is None:
            print("[DEBUG] No space found")
            return

        entities = getattr(space, '_entity_agents', {})
        print(f"[DEBUG] Found {len(entities)} entities in space")

        for entity in entities.keys():
            if isinstance(entity, Conveyor) and hasattr(entity, 'points') and len(entity.points) >= 2:
                x = [p[0] for p in entity.points]
                y = [p[1] for p in entity.points]
                label = getattr(entity, 'name', 'Conveyor')
                print(f"[DEBUG] Drawing {label}: {list(zip(x, y))}")
                self.ax.plot(x, y, 'b-', linewidth=2, label=label)
                self.ax.scatter(x[0], y[0], c='green', s=50, zorder=5, marker='o')  # Start
                self.ax.scatter(x[-1], y[-1], c='red', s=50, zorder=5, marker='s')  # End

        self.ax.legend()
        self._conveyors_drawn = True

    def render_tick(self, tick: int):
        """Update visualization — draw conveyors once, then update agents."""
        try:
            # Draw conveyors if not done yet
            if not self._conveyors_drawn:
                self._draw_conveyors()

            # Clear only agent-related elements
            if self.agent_scatter:
                self.agent_scatter.remove()
            for ann in self.agent_annotations:
                ann.remove()
            self.agent_annotations.clear()

            # Draw agents
            agent_x = []
            agent_y = []
            agent_labels = []

            for agent in getattr(self.simulator, 'agents', []):
                state = agent.space_state
                if state and "entity" in state and "progress_on_entity" in state:
                    entity = state["entity"]
                    if hasattr(entity, 'get_position_at_progress'):
                        progress = state["progress_on_entity"]
                        pos = entity.get_position_at_progress(progress)
                        agent_x.append(pos[0])
                        agent_y.append(pos[1])
                        agent_labels.append(f"A{id(agent) % 1000}")

            if agent_x:
                self.agent_scatter = self.ax.scatter(
                    agent_x, agent_y,
                    c='orange', s=100, zorder=10,
                    edgecolors='black', linewidth=1,
                    label='Agents'
                )
                for i, label in enumerate(agent_labels):
                    ann = self.ax.annotate(
                        label,
                        (agent_x[i], agent_y[i]),
                        textcoords="offset points",
                        xytext=(0, 10),
                        ha='center',
                        fontsize=9,
                        zorder=11
                    )
                    self.agent_annotations.append(ann)

            self.ax.set_title(f"Conveyor System - Tick {tick}")
            plt.pause(1)

        except Exception as e:
            print(f"[MatplotlibViewer] Error at tick {tick}: {e}", file=sys.stderr)

    def show_final(self):
        plt.ioff()
        plt.show()
