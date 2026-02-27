"""
Simple Pygame 3D viewer for spaces (NoCollisionSpace and CollisionSpace)
Displays agents in 3D space as points that can be rotated, panned, and zoomed
Draws obstacles from CollisionSpace as prisms
Supports ColoredSpace rectangles as prisms with alpha transparency
"""

import pygame
import sys
import math
from typing import Dict, Tuple
from aim.core.agent import BaseAgent

class Pygame3DViewer:
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

        pygame.display.set_caption("3D Agent Viewer")
        self.clock = pygame.time.Clock()

        # Camera settings - start from top-left corner
        self.camera_distance = 0
        self.camera_angle_x = 0  # Rotation around X-axis (vertical rotation)
        self.camera_angle_y = 0  # Rotation around Y-axis (horizontal rotation)
        self.camera_offset_x = 0
        self.camera_offset_y = 0
        self.camera_offset_z = 0
        self.zoom = 20.0

        # Colors
        self.background_color = (255, 255, 255)  # White background
        self.axis_color = (0, 0, 0)    # Black axes
        self.agent_color = (255, 0, 0)     # Red agents
        self.obstacle_color = (150, 150, 150) # Gray obstacles

        # For handling pygame events
        self.dragging = False
        self.drag_button = 0  # 1 for left button, 3 for right button
        self.last_mouse_pos = (0, 0)
        self.pan_speed = 0.5   # Speed of panning (increased)

    def project_3d_to_2d(self, x: float, y: float, z: float) -> Tuple[float, float]:
        """
        Project 3D coordinates to 2D screen coordinates
        This is a simple orthographic projection with camera transformations
        """
        # Apply camera offset (translation)
        x -= self.camera_offset_x
        y -= self.camera_offset_y
        z -= self.camera_offset_z

        # Apply camera rotation
        # Rotate around Y-axis
        x_rot = x * math.cos(self.camera_angle_y) - z * math.sin(self.camera_angle_y)
        z_rot = x * math.sin(self.camera_angle_y) + z * math.cos(self.camera_angle_y)

        # Rotate around X-axis
        y_rot = y * math.cos(self.camera_angle_x) - z_rot * math.sin(self.camera_angle_x)
        z_rot_final = y * math.sin(self.camera_angle_x) + z_rot * math.cos(self.camera_angle_x)

        # Apply zoom
        x_screen = x_rot * self.zoom
        y_screen = y_rot * self.zoom

        # Center on screen
        x_screen = self.width // 2 + x_screen
        y_screen = self.height // 2 - y_screen  # Invert Y-axis for pygame

        return x_screen, y_screen

    def render_tick(self, tick: int):
        """Render the current simulation state"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in [1, 3]:  # Left or right mouse button
                    self.dragging = True
                    self.drag_button = event.button
                    self.last_mouse_pos = event.pos
                elif event.button == 4:  # Mouse wheel up / touchpad scroll up
                    self.zoom *= 1.1
                elif event.button == 5:  # Mouse wheel down / touchpad scroll down
                    self.zoom *= 0.9
                elif event.button == 6:  # Touchpad scroll left
                    self.zoom *= 0.95
                elif event.button == 7:  # Touchpad scroll right
                    self.zoom *= 1.05
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button in [1, 3]:  # Left or right mouse button
                    self.dragging = False
                    self.drag_button = 0
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    dx = event.pos[0] - self.last_mouse_pos[0]
                    dy = event.pos[1] - self.last_mouse_pos[1]

                    if self.drag_button == 1:  # Left mouse button - pan
                        # Adjust panning speed based on zoom level
                        pan_factor = self.pan_speed / self.zoom
                        self.camera_offset_x -= dx * pan_factor
                        self.camera_offset_y += dy * pan_factor
                    elif self.drag_button == 3:  # Right mouse button - rotate
                        # Adjust rotation speed
                        self.camera_angle_y += dx * 0.01
                        self.camera_angle_x += dy * 0.01

                    self.last_mouse_pos = event.pos
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # Clear screen
        self.screen.fill(self.background_color)

        # Draw coordinate axes for reference
        self.draw_axes()

        # Draw obstacles from CollisionSpace if available
        self._draw_obstacles()

        # Draw agents
        for agent in self.simulator.agents:
            if hasattr(agent, 'space_state') and agent.space_state:
                pos = agent.space_state.get("position")
                if pos and len(pos) == 3:
                    x, y, z = pos
                    screen_x, screen_y = self.project_3d_to_2d(x, y, z)

                    # Draw agent as a point
                    # Use agent's color if available, otherwise default color
                    agent_color = getattr(agent, 'color', self.agent_color)
                    pygame.draw.circle(self.screen, agent_color, (int(screen_x), int(screen_y)), 5)

        # Update display
        pygame.display.flip()
        self.clock.tick(10) # Cap at 10 FPS

    def _draw_obstacles(self):
        """Draw obstacles from CollisionSpace and ColoredSpace if available"""
        if hasattr(self.simulator, 'spaces'):
            for space_name, space in self.simulator.spaces.items():
                # Check if the space has obstacles (CollisionSpace or ColoredSpace)
                if hasattr(space, '_obstacles') and space._obstacles:
                    for obstacle in space._obstacles:
                        if obstacle is not None:  # Skip removed obstacles
                            self._draw_prism(obstacle)

    def _draw_prism(self, prism):
        """
        Draw a prism obstacle in 3D space.
        Supports both formats:
        - CollisionSpace: (points_3d, height)
        - ColoredSpace: (points_3d, height, color, alpha)
        """
        # Check if prism has color/alpha (ColoredSpace) or just geometry (CollisionSpace)
        if len(prism) == 4:
            points_3d, height, color, alpha = prism
        else:
            points_3d, height = prism
            color = self.obstacle_color
            alpha = 255

        if len(points_3d) < 3:
            return  # Not a valid polygon

        # Draw the base polygon
        base_screen_points = []
        for point in points_3d:
            x, y, z = point
            screen_x, screen_y = self.project_3d_to_2d(x, y, z)
            base_screen_points.append((int(screen_x), int(screen_y)))

        if len(base_screen_points) > 2:
            # Create surface for alpha support
            if alpha < 255:
                # Use pygame.Surface with SRCALPHA for transparency
                base_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                pygame.draw.polygon(base_surface, (*color, alpha), base_screen_points)
                self.screen.blit(base_surface, (0, 0))
            else:
                pygame.draw.polygon(self.screen, color, base_screen_points)
            pygame.draw.polygon(self.screen, (200, 200, 200), base_screen_points, 2)  # Border

        # Draw the top polygon (at base Z + height)
        top_screen_points = []
        for point in points_3d:
            x, y, z = point
            # Assuming height is added to the Z coordinate
            top_z = z + height
            screen_x, screen_y = self.project_3d_to_2d(x, y, top_z)
            top_screen_points.append((int(screen_x), int(screen_y)))

        if len(top_screen_points) > 2:
            if alpha < 255:
                top_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                pygame.draw.polygon(top_surface, (*color, alpha), top_screen_points)
                self.screen.blit(top_surface, (0, 0))
            else:
                pygame.draw.polygon(self.screen, color, top_screen_points)
            pygame.draw.polygon(self.screen, (200, 200, 200), top_screen_points, 2)  # Border

        # Draw vertical lines connecting base and top
        for i in range(len(points_3d)):
            base_point = points_3d[i]
            top_point = (points_3d[i][0], points_3d[i][1], points_3d[i][2] + height)

            base_x, base_y = self.project_3d_to_2d(base_point[0], base_point[1], base_point[2])
            top_x, top_y = self.project_3d_to_2d(top_point[0], top_point[1], top_point[2])

            pygame.draw.line(self.screen, (200, 200, 200), (int(base_x), int(base_y)), (int(top_x), int(top_y)), 2)

    def draw_axes(self):
        """Draw coordinate axes for reference"""
        # Draw X-axis (red)
        start_x, start_y = self.project_3d_to_2d(0, 0, 0)
        end_x, end_y = self.project_3d_to_2d(5, 0, 0)  # 5 units in X direction
        pygame.draw.line(self.screen, (255, 0, 0), (start_x, start_y), (end_x, end_y), 2)

        # Draw Y-axis (green)
        start_x, start_y = self.project_3d_to_2d(0, 0, 0)
        end_x, end_y = self.project_3d_to_2d(0, 5, 0)  # 5 units in Y direction
        pygame.draw.line(self.screen, (0, 255, 0), (start_x, start_y), (end_x, end_y), 2)

        # Draw Z-axis (blue)
        start_x, start_y = self.project_3d_to_2d(0, 0, 0)
        end_x, end_y = self.project_3d_to_2d(0, 0, 5)  # 5 units in Z direction
        pygame.draw.line(self.screen, (0, 0, 255), (start_x, start_y), (end_x, end_y), 2)

    def show_final(self):
        """Keep the window open after simulation ends with full navigation support"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button in [1, 3]:  # Left or right mouse button
                        self.dragging = True
                        self.drag_button = event.button
                        self.last_mouse_pos = event.pos
                    elif event.button == 4:  # Mouse wheel up / touchpad scroll up
                        self.zoom *= 1.1
                    elif event.button == 5:  # Mouse wheel down / touchpad scroll down
                        self.zoom *= 0.9
                    elif event.button == 6:  # Touchpad scroll left
                        self.zoom *= 0.95
                    elif event.button == 7:  # Touchpad scroll right
                        self.zoom *= 1.05
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button in [1, 3]:  # Left or right mouse button
                        self.dragging = False
                        self.drag_button = 0
                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging:
                        dx = event.pos[0] - self.last_mouse_pos[0]
                        dy = event.pos[1] - self.last_mouse_pos[1]

                        if self.drag_button == 1:  # Left mouse button - pan
                            # Adjust panning speed based on zoom level
                            pan_factor = self.pan_speed / self.zoom
                            self.camera_offset_x -= dx * pan_factor
                            self.camera_offset_y += dy * pan_factor
                        elif self.drag_button == 3:  # Right mouse button - rotate
                            # Adjust rotation speed
                            self.camera_angle_y += dx * 0.01
                            self.camera_angle_x += dy * 0.01

                        self.last_mouse_pos = event.pos
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            # Continue rendering with current state
            self.screen.fill(self.background_color)
            self.draw_axes()

            # Draw obstacles
            self._draw_obstacles()

            # Draw agents
            for agent in self.simulator.agents:
                if hasattr(agent, 'space_state') and agent.space_state:
                    pos = agent.space_state.get("position")
                    if pos and len(pos) == 3:
                        x, y, z = pos
                        screen_x, screen_y = self.project_3d_to_2d(x, y, z)

                        # Draw agent as a point
                        # Use agent's color if available, otherwise default color
                        agent_color = getattr(agent, 'color', self.agent_color)
                        pygame.draw.circle(self.screen, agent_color, (int(screen_x), int(screen_y)), 5)

            pygame.display.flip()
            self.clock.tick(60)  # Cap at 60 FPS

        pygame.quit()
