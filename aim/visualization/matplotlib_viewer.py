import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
from matplotlib.colors import to_hex
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
        """Draw all conveyors from all spaces — called once, lazily."""
        if self._conveyors_drawn:
            return

        spaces = getattr(self.simulator, 'spaces', {})
        if not spaces:
            print("[DEBUG] No spaces found")
            return

        # Create a color map — assign color based on conveyor name

        # Use tab20 for up to 20 distinct colors, then cycle
        cmap = get_cmap('tab20')
        color_cache = {}

        for space_name, space in spaces.items():
            entities = getattr(space, '_entity_agents', {})
            for entity in entities.keys():
                if isinstance(entity, Conveyor) and hasattr(entity, 'points') and len(entity.points) >= 2:
                    x = [p[0] for p in entity.points]
                    y = [p[1] for p in entity.points]
                    label = getattr(entity, 'name', 'Conveyor')

                    # Generate consistent color based on name
                    if label not in color_cache:
                        # Hash name to index, mod 20 for tab20
                        hash_val = hash(label) % 20
                        color = to_hex(cmap(hash_val))
                        color_cache[label] = color
                    color = color_cache[label]

                    # Draw full path line with unique color
                    self.ax.plot(x, y, color=color, linewidth=2, label=f"{label} ({space_name})")

                    # Mark EVERY point in the path
                    self.ax.scatter(x, y, c=color, s=30, zorder=4, marker='x', alpha=0.7)

                    # Highlight start and end
                    self.ax.scatter(x[0], y[0], c='green', s=50, zorder=5, marker='o')
                    self.ax.scatter(x[-1], y[-1], c='red', s=50, zorder=5, marker='s')

        # Avoid duplicate labels
        handles, labels = self.ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        self.ax.legend(by_label.values(), by_label.keys())

        self._conveyors_drawn = True

    def render_tick(self, tick: int):
        """Update visualization — draw conveyors once, then update agents."""
        try:
            if not self._conveyors_drawn:
                self._draw_conveyors()

            # Clear only agent-related elements — safely
            if self.agent_scatter:
                try:
                    self.agent_scatter.remove()
                except ValueError:
                    # Artist already removed — ignore
                    pass
                self.agent_scatter = None

            for ann in self.agent_annotations:
                try:
                    ann.remove()
                except ValueError:
                    pass
            self.agent_annotations.clear()

            # Draw agents
            agent_x = []
            agent_y = []
            agent_labels = []

            for agent in getattr(self.simulator, 'agents', []):
                state = agent.space_state
                if state and "position" in state:
                    pos = state["position"]
                    agent_x.append(pos[0])
                    agent_y.append(pos[1])
                    agent_labels.append(f"A{id(agent) % 1000}")
                elif state and "entity" in state and "progress_on_entity" in state:
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

            self.ax.set_title(f"Simulation - Tick {tick}")
            plt.pause(1)

        except Exception as e:
            print(f"[MatplotlibViewer] Error at tick {tick}: {e}", file=sys.stderr)

    def show_final(self):
        plt.ioff()
        plt.show()
