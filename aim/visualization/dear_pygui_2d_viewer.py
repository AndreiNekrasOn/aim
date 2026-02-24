"""
GPU-accelerated 2D viewer using Dear PyGui.
Much faster than pygame for large numbers of obstacles.
"""

from typing import Optional, List, Tuple
from aim.core.agent import BaseAgent

import dearpygui.dearpygui as dpg


class DearPyGui2DViewer:
    """
    2D top-down viewer using Dear PyGui (GPU-accelerated).

    Controls:
    - Mouse wheel: Zoom in/out
    - Middle mouse drag: Pan
    - ESC: Close window
    """

    def __init__(self, simulator, width: int = 1920, height: int = 1080):
        self.simulator = simulator
        self.width = width
        self.height = height

        # Camera for pan/zoom (world coordinates)
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.zoom = 1.0

        # Colors
        self.agent_color = (255, 0, 0, 255)  # Red agents (RGBA)
        self.default_obstacle_color = (0, 200, 0, 200)  # Green obstacles

        # Dear PyGui setup
        dpg.create_context()

        # Create viewport
        dpg.create_viewport(
            title='Warehouse 2D Viewer',
            width=width,
            height=height,
            vsync=True
        )

        # Create main window
        with dpg.window(
            label="Warehouse",
            width=width,
            height=height,
            pos=(0, 0),
            movable=False,
            resizable=False,
            no_title_bar=True,
            no_collapse=True,
            no_resize=True
        ):
            # Drawlist for rendering
            self.drawlist = dpg.add_drawlist(width, height)

        # Track obstacle nodes (for deletion on zoom/pan)
        self._obstacle_nodes: List[int] = []
        self._agent_nodes: List[int] = []

        # Setup keyboard shortcuts
        with dpg.handler_registry():
            dpg.add_key_release_handler(dpg.mvKey_Escape, callback=lambda: dpg.stop_dearpygui())

        dpg.setup_dearpygui()
        dpg.show_viewport()

        # Build obstacle visualization once
        self._build_obstacles()

    def _build_obstacles(self):
        """Render all obstacles once to the drawlist."""
        # Clear existing obstacles
        for node in self._obstacle_nodes:
            dpg.delete_item(node)
        self._obstacle_nodes.clear()

        # Collect and draw obstacles
        if hasattr(self.simulator, 'spaces'):
            for space in self.simulator.spaces.values():
                if hasattr(space, '_obstacles'):
                    for obstacle in space._obstacles:
                        if obstacle is None:
                            continue

                        # Parse obstacle format
                        if len(obstacle) == 4:
                            points, _, color, alpha = obstacle
                            color = tuple(color) + (alpha,)  # Convert to RGBA
                        else:
                            points, _ = obstacle
                            color = self.default_obstacle_color

                        # Convert to screen coordinates
                        xs = []
                        ys = []
                        for p in points:
                            screen_x, screen_y = self.world_to_screen(p[0], p[1])
                            xs.append(screen_x)
                            ys.append(screen_y)

                        if len(xs) >= 3:
                            node = dpg.draw_polygon(
                                list(zip(xs, ys)),
                                fill=color,
                                parent=self.drawlist
                            )
                            self._obstacle_nodes.append(node)

    def world_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        """Convert world coordinates to screen coordinates."""
        screen_x = (x - self.camera_x) * self.zoom + self.width // 2
        screen_y = (y - self.camera_y) * self.zoom + self.height // 2
        return screen_x, screen_y

    def screen_to_world(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates."""
        world_x = (screen_x - self.width // 2) / self.zoom + self.camera_x
        world_y = (screen_y - self.height // 2) / self.zoom + self.camera_y
        return world_x, world_y

    def _update_agents(self):
        """Update agent positions on screen."""
        # Clear existing agent nodes
        for node in self._agent_nodes:
            dpg.delete_item(node)
        self._agent_nodes.clear()

        # Draw agents
        for agent in self.simulator.agents:
            if hasattr(agent, 'space_state') and agent.space_state:
                pos = agent.space_state.get("position")
                if pos and len(pos) >= 2:
                    screen_x, screen_y = self.world_to_screen(pos[0], pos[1])

                    # Get agent color
                    agent_color = getattr(agent, 'color', self.agent_color)
                    if len(agent_color) == 3:
                        agent_color = tuple(agent_color) + (255,)

                    # Draw agent as circle
                    node = dpg.draw_circle(
                        (screen_x, screen_y),
                        5 * self.zoom,  # Scale radius with zoom
                        fill=agent_color,
                        parent=self.drawlist
                    )
                    self._agent_nodes.append(node)

    def render_tick(self, tick: int):
        """Render the current simulation state."""
        # Update agents (obstacles are static)
        self._update_agents()

        # Render frame
        dpg.render_dearpygui_frame()

    def show_final(self):
        """Keep window open after simulation with navigation."""
        # Setup mouse handlers for navigation
        def on_mouse_wheel(sender, app_data):
            # Zoom toward mouse position
            mouse_x, mouse_y = dpg.get_mouse_pos()
            mouse_world = self.screen_to_world(mouse_x, mouse_y)

            if app_data > 0:
                self.zoom *= 1.1
            else:
                self.zoom *= 0.9

            # Adjust camera to zoom toward mouse
            self.camera_x = mouse_world[0] - (mouse_x - self.width // 2) / self.zoom
            self.camera_y = mouse_world[1] - (mouse_y - self.height // 2) / self.zoom

            # Rebuild obstacles at new zoom level
            self._build_obstacles()

        def on_middle_mouse_drag(sender, app_data):
            # Pan camera
            if app_data[1]:  # Middle mouse button is pressed
                dx, dy = app_data[2], app_data[3]
                self.camera_x -= dx / self.zoom
                self.camera_y -= dy / self.zoom

                # Rebuild obstacles at new position
                self._build_obstacles()

        # Register handlers
        with dpg.handler_registry():
            dpg.add_mouse_wheel_handler(callback=on_mouse_wheel)
            dpg.add_mouse_drag_handler(dpg.mvMouseButton_Middle, callback=on_middle_mouse_drag)

        # Main loop
        while dpg.is_dearpygui_running():
            # Update agents
            self._update_agents()
            dpg.render_dearpygui_frame()

        dpg.destroy_context()
