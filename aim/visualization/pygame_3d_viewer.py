"""
Simple Pygame 3D viewer for NoCollisionSpace
Displays agents in 3D space as points that can be rotated and zoomed
"""

import pygame
import sys
import math
from typing import Dict, Tuple
from aim.core.agent import BaseAgent

class Pygame3DViewer:
    def __init__(self, simulator, width: int = 800, height: int = 600):
        self.simulator = simulator
        self.width = width
        self.height = height

        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("3D Agent Viewer")
        self.clock = pygame.time.Clock()

        # Camera settings
        self.camera_distance = 10
        self.camera_angle_x = 0  # Rotation around X-axis (vertical rotation)
        self.camera_angle_y = 0  # Rotation around Y-axis (horizontal rotation)
        self.zoom = 1.0

        # Colors
        self.background_color = (0, 0, 0)  # Dark blue background
        self.axis_color = (255, 255, 255)  # White axes

        # For handling pygame events
        self.dragging = False
        self.last_mouse_pos = (0, 0)

    def project_3d_to_2d(self, x: float, y: float, z: float) -> Tuple[float, float]:
        """
        Project 3D coordinates to 2D screen coordinates
        This is a simple orthographic projection
        """
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
                if event.button == 1:  # Left mouse button
                    self.dragging = True
                    self.last_mouse_pos = event.pos
                elif event.button == 4:  # Mouse wheel up
                    self.zoom *= 1.1
                elif event.button == 5:  # Mouse wheel down
                    self.zoom *= 0.9
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    self.dragging = False
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    dx = event.pos[0] - self.last_mouse_pos[0]
                    dy = event.pos[1] - self.last_mouse_pos[1]

                    # Adjust rotation speed
                    self.camera_angle_y += dx * 0.01
                    self.camera_angle_x += dy * 0.01

                    self.last_mouse_pos = event.pos

        # Clear screen
        self.screen.fill(self.background_color)

        # Draw coordinate axes for reference
        self.draw_axes()

        # Draw agents
        for agent in self.simulator.agents:
            if hasattr(agent, 'space_state') and agent.space_state:
                pos = agent.space_state.get("position")
                if pos and len(pos) == 3:
                    x, y, z = pos
                    screen_x, screen_y = self.project_3d_to_2d(x, y, z)

                    # Draw agent as a point
                    pygame.draw.circle(self.screen, agent.color, (int(screen_x), int(screen_y)), 5)

        # Update display
        pygame.display.flip()
        self.clock.tick(10) # Cap at 10 FPS

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
                    if event.button == 1:  # Left mouse button
                        self.dragging = True
                        self.last_mouse_pos = event.pos
                    elif event.button == 4:  # Mouse wheel up
                        self.zoom *= 1.1
                    elif event.button == 5:  # Mouse wheel down
                        self.zoom *= 0.9
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:  # Left mouse button
                        self.dragging = False
                elif event.type == pygame.MOUSEMOTION:
                    if self.dragging:
                        dx = event.pos[0] - self.last_mouse_pos[0]
                        dy = event.pos[1] - self.last_mouse_pos[1]

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

            # Draw agents
            for agent in self.simulator.agents:
                if hasattr(agent, 'space_state') and agent.space_state:
                    pos = agent.space_state.get("position")
                    if pos and len(pos) == 3:
                        x, y, z = pos
                        screen_x, screen_y = self.project_3d_to_2d(x, y, z)

                        # Draw agent as a point
                        pygame.draw.circle(self.screen, agent.color, (int(screen_x), int(screen_y)), 5)

            pygame.display.flip()
            self.clock.tick(60)  # Cap at 60 FPS

        pygame.quit()
