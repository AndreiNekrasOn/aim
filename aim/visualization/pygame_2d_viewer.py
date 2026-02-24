"""
Simple Pygame 2D top-down viewer for warehouse simulation.
Much faster than 3D viewer - no projection math, just 2D transforms.
"""

import pygame
import sys
from typing import Dict, Tuple, List, Optional
from aim.core.agent import BaseAgent


class Pygame2DViewer:
    """
    2D top-down viewer for warehouse simulation.

    Controls:
    - Left mouse drag: Pan
    - Mouse wheel: Zoom in/out
    - Right mouse drag: Also pan (alternative)
    - ESC: Close window
    """

    def __init__(self, simulator, width: int = 0, height: int = 0):
        self.simulator = simulator

        # Fullscreen by default
        if width == 0 or height == 0:
            pygame.init()
            info = pygame.display.Info()
            self.width = info.current_w
            self.height = info.current_h
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        else:
            self.width = width
            self.height = height
            pygame.init()
            self.screen = pygame.display.set_mode((width, height))

        pygame.display.set_caption("Warehouse 2D Viewer")
        self.clock = pygame.time.Clock()

        # Camera for 2D pan/zoom (world coordinates)
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.zoom = 10.0

        # Colors
        self.background_color = (255, 255, 255)  # White background
        self.agent_color = (255, 0, 0)  # Red agents
        self.default_obstacle_color = (0, 200, 0)  # Green obstacles

        # Mouse handling
        self.dragging = False
        self.last_mouse_pos = (0, 0)

        # Cached obstacle surface (for performance)
        self._obstacle_surface: Optional[pygame.Surface] = None
        self._obstacles_dirty = True

        # Viewport bounds (world coordinates)
        self._viewport_left = 0.0
        self._viewport_right = 0.0
        self._viewport_top = 0.0
        self._viewport_bottom = 0.0
        self._update_viewport_bounds()

    def world_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates."""
        screen_x = (x - self.camera_x) * self.zoom + self.width // 2
        screen_y = (y - self.camera_y) * self.zoom + self.height // 2
        return int(screen_x), int(screen_y)

    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates."""
        world_x = (screen_x - self.width // 2) / self.zoom + self.camera_x
        world_y = (screen_y - self.height // 2) / self.zoom + self.camera_y
        return world_x, world_y

    def _update_viewport_bounds(self):
        """Calculate world coordinate bounds of visible viewport."""
        half_width = (self.width / 2) / self.zoom
        half_height = (self.height / 2) / self.zoom
        self._viewport_left = self.camera_x - half_width
        self._viewport_right = self.camera_x + half_width
        self._viewport_top = self.camera_y - half_height
        self._viewport_bottom = self.camera_y + half_height

    def _is_in_viewport(self, points: List[Tuple[float, float]]) -> bool:
        """Check if any point of polygon is visible in viewport."""
        for x, y in points:
            if (self._viewport_left <= x <= self._viewport_right and
                self._viewport_top <= y <= self._viewport_bottom):
                return True
        return False

    def _ensure_obstacle_surface(self):
        """Pre-render obstacles to surface for performance."""
        if not self._obstacles_dirty and self._obstacle_surface is not None:
            return

        # Create obstacle surface
        self._obstacle_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._obstacle_surface.fill((255, 255, 255, 0))  # Transparent

        # Collect all obstacles
        obstacles_to_draw = []
        if hasattr(self.simulator, 'spaces'):
            for space in self.simulator.spaces.values():
                if hasattr(space, '_obstacles') and space._obstacles:
                    for obstacle in space._obstacles:
                        if obstacle is not None:
                            obstacles_to_draw.append(obstacle)

        # Draw all obstacles to surface
        for obstacle in obstacles_to_draw:
            # Parse obstacle format
            if len(obstacle) == 4:
                # ColoredSpace format: (points, height, color, alpha)
                points, _, color, alpha = obstacle
            else:
                # CollisionSpace format: (points, height)
                points, _ = obstacle
                color = self.default_obstacle_color
                alpha = 200

            # Convert to screen coordinates
            screen_points = [self.world_to_screen(p[0], p[1]) for p in points]

            if len(screen_points) >= 3:
                # Create surface for alpha blending
                if alpha < 255:
                    # Calculate bounding box
                    min_x = min(p[0] for p in screen_points)
                    max_x = max(p[0] for p in screen_points)
                    min_y = min(p[1] for p in screen_points)
                    max_y = max(p[1] for p in screen_points)

                    surf_width = max(1, max_x - min_x + 2)
                    surf_height = max(1, max_y - min_y + 2)

                    poly_surface = pygame.Surface((surf_width, surf_height), pygame.SRCALPHA)
                    local_points = [(p[0] - min_x, p[1] - min_y) for p in screen_points]
                    pygame.draw.polygon(poly_surface, (*color, alpha), local_points)
                    self._obstacle_surface.blit(poly_surface, (min_x, min_y))
                else:
                    pygame.draw.polygon(self._obstacle_surface, color, screen_points)

        self._obstacles_dirty = False

    def render_tick(self, tick: int):
        """Render the current simulation state."""
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in [1, 3]:  # Left or right mouse button
                    self.dragging = True
                    self.last_mouse_pos = event.pos
                elif event.button == 4:  # Mouse wheel up
                    old_zoom = self.zoom
                    self.zoom *= 1.1
                    # Zoom toward mouse position
                    mouse_world = self.screen_to_world(event.pos[0], event.pos[1])
                    self.camera_x = mouse_world[0] - (event.pos[0] - self.width // 2) / self.zoom
                    self.camera_y = mouse_world[1] - (event.pos[1] - self.height // 2) / self.zoom
                    self._update_viewport_bounds()
                    self._obstacles_dirty = True
                elif event.button == 5:  # Mouse wheel down
                    old_zoom = self.zoom
                    self.zoom *= 0.9
                    # Zoom toward mouse position
                    mouse_world = self.screen_to_world(event.pos[0], event.pos[1])
                    self.camera_x = mouse_world[0] - (event.pos[0] - self.width // 2) / self.zoom
                    self.camera_y = mouse_world[1] - (event.pos[1] - self.height // 2) / self.zoom
                    self._update_viewport_bounds()
                    self._obstacles_dirty = True
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button in [1, 3]:
                    self.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    dx = event.pos[0] - self.last_mouse_pos[0]
                    dy = event.pos[1] - self.last_mouse_pos[1]
                    # Pan camera (inverted - drag moves opposite direction)
                    self.camera_x -= dx / self.zoom
                    self.camera_y -= dy / self.zoom
                    self.last_mouse_pos = event.pos
                    self._update_viewport_bounds()
                    self._obstacles_dirty = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # Clear screen
        self.screen.fill(self.background_color)

        # Draw pre-rendered obstacles
        self._ensure_obstacle_surface()
        if self._obstacle_surface:
            self.screen.blit(self._obstacle_surface, (0, 0))

        # Draw agents (dynamic - redrawn every frame)
        for agent in self.simulator.agents:
            if hasattr(agent, 'space_state') and agent.space_state:
                pos = agent.space_state.get("position")
                if pos and len(pos) >= 2:
                    screen_x, screen_y = self.world_to_screen(pos[0], pos[1])

                    # Check if agent is visible
                    if (0 <= screen_x < self.width and 0 <= screen_y < self.height):
                        # Use agent's color if available
                        agent_color = getattr(agent, 'color', self.agent_color)
                        pygame.draw.circle(self.screen, agent_color, (screen_x, screen_y), 5)

        # Draw viewport info (optional - can remove for performance)
        self._draw_info(tick)

        # Update display
        pygame.display.flip()
        self.clock.tick(60)  # 60 FPS

    def _draw_info(self, tick: int):
        """Draw debug info overlay."""
        font = pygame.font.Font(None, 24)
        info_text = f"Tick: {tick} | Zoom: {self.zoom:.2f}x | Camera: ({self.camera_x:.1f}, {self.camera_y:.1f})"
        text_surface = font.render(info_text, True, (0, 0, 0))
        self.screen.blit(text_surface, (10, 10))

    def show_final(self):
        """Keep window open after simulation with navigation."""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button in [1, 3]:
                        self.dragging = True
                        self.last_mouse_pos = event.pos
                    elif event.button == 4:
                        old_zoom = self.zoom
                        self.zoom *= 1.1
                        mouse_world = self.screen_to_world(event.pos[0], event.pos[1])
                        self.camera_x = mouse_world[0] - (event.pos[0] - self.width // 2) / self.zoom
                        self.camera_y = mouse_world[1] - (event.pos[1] - self.height // 2) / self.zoom
                        self._update_viewport_bounds()
                        self._obstacles_dirty = True
                    elif event.button == 5:
                        old_zoom = self.zoom
                        self.zoom *= 0.9
                        mouse_world = self.screen_to_world(event.pos[0], event.pos[1])
                        self.camera_x = mouse_world[0] - (event.pos[0] - self.width // 2) / self.zoom
                        self.camera_y = mouse_world[1] - (event.pos[1] - self.height // 2) / self.zoom
                        self._update_viewport_bounds()
                        self._obstacles_dirty = True
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button in [1, 3]:
                        self.dragging = False
                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging:
                        dx = event.pos[0] - self.last_mouse_pos[0]
                        dy = event.pos[1] - self.last_mouse_pos[1]
                        self.camera_x -= dx / self.zoom
                        self.camera_y -= dy / self.zoom
                        self.last_mouse_pos = event.pos
                        self._update_viewport_bounds()
                        self._obstacles_dirty = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            self.screen.fill(self.background_color)
            self._ensure_obstacle_surface()
            if self._obstacle_surface:
                self.screen.blit(self._obstacle_surface, (0, 0))

            # Draw agents
            for agent in self.simulator.agents:
                if hasattr(agent, 'space_state') and agent.space_state:
                    pos = agent.space_state.get("position")
                    if pos and len(pos) >= 2:
                        screen_x, screen_y = self.world_to_screen(pos[0], pos[1])
                        if 0 <= screen_x < self.width and 0 <= screen_y < self.height:
                            agent_color = getattr(agent, 'color', self.agent_color)
                            pygame.draw.circle(self.screen, agent_color, (screen_x, screen_y), 5)

            self._draw_info(0)
            pygame.display.flip()
            self.clock.tick(0)

        pygame.quit()
