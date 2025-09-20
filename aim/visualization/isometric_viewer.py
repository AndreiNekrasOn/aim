import matplotlib.pyplot as plt
import sys
from aim.entities.manufacturing.conveyor import Conveyor
from matplotlib.cm import get_cmap
from matplotlib.colors import to_hex

class IsometricMatplotlibViewer:
    """
    Isometric 2D viewer for 3D conveyor systems.
    Projects 3D coordinates to 2D isometric view to show Z-axis depth.
    """

    def __init__(self, simulator):
        self.simulator = simulator
        self.fig, self.ax = plt.subplots(figsize=(14, 10))
        self.ax.set_title("Isometric View - Conveyor System")
        self.ax.set_xlabel("X (Isometric)")
        self.ax.set_ylabel("Y (Isometric)")
        self.ax.grid(True, alpha=0.3)
        plt.ion()

        # Agent scatter
        self.agent_scatter = None
        self.agent_annotations = []
        self._conveyors_drawn = False

        # Color map for conveyors
        self.cmap = get_cmap('tab20')
        self.color_cache = {}

    def _project_isometric(self, x: float, y: float, z: float) -> tuple[float, float]:
        """
        Convert 3D point to 2D isometric projection.
        """
        # Isometric projection: 30 degree tilt
        x_iso = x - z * 0.866  # cos(30°)
        y_iso = y - z * 0.5    # sin(30°)
        return x_iso, y_iso

    def _draw_conveyors(self):
        """Draw all conveyors in isometric view."""
        if self._conveyors_drawn:
            return

        spaces = getattr(self.simulator, 'spaces', {})
        if not spaces:
            return

        for space_name, space in spaces.items():
            entities = getattr(space, '_entity_agents', {})
            for entity in entities.keys():
                if isinstance(entity, Conveyor) and hasattr(entity, 'points') and len(entity.points) >= 2:
                    # Project all points to isometric view
                    iso_points = [self._project_isometric(p[0], p[1], p[2]) for p in entity.points]
                    x_iso = [p[0] for p in iso_points]
                    y_iso = [p[1] for p in iso_points]
                    label = getattr(entity, 'name', 'Conveyor')

                    # Assign color
                    if label not in self.color_cache:
                        hash_val = hash(label) % 20
                        color = to_hex(self.cmap(hash_val))
                        self.color_cache[label] = color
                    color = self.color_cache[label]

                    # Draw conveyor path
                    self.ax.plot(x_iso, y_iso, color=color, linewidth=2, label=f"{label} (Z={entity.points[0][2]:.1f})")

                    # Mark points
                    self.ax.scatter(x_iso, y_iso, c=color, s=25, marker='x', alpha=0.7)

                    # Highlight start (green) and end (red)
                    self.ax.scatter(x_iso[0], y_iso[0], c='lime', s=60, marker='o', edgecolors='black', linewidth=1)
                    self.ax.scatter(x_iso[-1], y_iso[-1], c='red', s=60, marker='s', edgecolors='black', linewidth=1)

        # Legend
        handles, labels = self.ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        self.ax.legend(by_label.values(), by_label.keys(), fontsize=8)

        self._conveyors_drawn = True

    def render_tick(self, tick: int):
        """Update isometric visualization."""
        try:
            if not self._conveyors_drawn:
                self._draw_conveyors()

            # Clear agents
            if self.agent_scatter:
                try:
                    self.agent_scatter.remove()
                except ValueError:
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
                    x_iso, y_iso = self._project_isometric(pos[0], pos[1], pos[2])
                    agent_x.append(x_iso)
                    agent_y.append(y_iso)
                    agent_labels.append(f"A{id(agent) % 1000}")
                elif state and "entity" in state and "progress_on_entity" in state:
                    entity = state["entity"]
                    if hasattr(entity, 'get_position_at_progress'):
                        progress = state["progress_on_entity"]
                        pos_3d = entity.get_position_at_progress(progress)
                        x_iso, y_iso = self._project_isometric(pos_3d[0], pos_3d[1], pos_3d[2])
                        agent_x.append(x_iso)
                        agent_y.append(y_iso)
                        agent_labels.append(f"A{id(agent) % 1000}")

            if agent_x:
                self.agent_scatter = self.ax.scatter(
                    agent_x, agent_y,
                    c='orange', s=120, zorder=10,
                    edgecolors='black', linewidth=1.5,
                    label='Agents'
                )
                for i, label in enumerate(agent_labels):
                    ann = self.ax.annotate(
                        label,
                        (agent_x[i], agent_y[i]),
                        textcoords="offset points",
                        xytext=(0, 12),
                        ha='center',
                        fontsize=9,
                        zorder=11,
                        weight='bold'
                    )
                    self.agent_annotations.append(ann)

            self.ax.set_title(f"Isometric View - Tick {tick}")
            plt.pause(0.0001)

        except Exception as e:
            print(f"[IsometricViewer] Error at tick {tick}: {e}", file=sys.stderr)

    def show_final(self):
        plt.ioff()
        plt.show()
