from typing import Dict, Any, List, Optional, Set, Tuple
from aim.core.space import SpaceManager
from aim.core.agent import BaseAgent

Point3D = Tuple[float, float, float]

# Prism definition: list of points forming the base polygon and height
Prism = Tuple[List[Point3D], float]

Path = List[Point3D]

class CollisionSpace(SpaceManager):
    """
    Manages agents moving in 3D space with collisions and obstacles.
    Agents move at constant speed toward target position with pathfinding and obstacle avoidance.
    Supports agent paths.
    """

    def __init__(self, obstacles: Optional[List[Prism]] = None):
        # Agent -> current position
        self._agent_position: Dict[BaseAgent, Point3D] = {}
        # Agent -> target position
        self._agent_target: Dict[BaseAgent, Point3D] = {}
        # Agent -> speed
        self._agent_speed: Dict[BaseAgent, float] = {}
        # Agent -> current path (list of waypoints)
        self._agent_path: Dict[BaseAgent, Path] = {}
        # List of obstacles in the space
        self._obstacles: List[Prism] = obstacles or []

    def register(self, agent: BaseAgent, initial_state: Dict[str, Any]) -> bool:
        """
        Register agent with initial state.
        Expected keys: "start_position", "target_position", "speed".
        """
        start_position = initial_state.get("start_position")
        target_position = initial_state.get("target_position")
        speed = initial_state.get("speed", 1.0)
        path = initial_state.get("path")

        if start_position is None or target_position is None:
            return False

        if not isinstance(start_position, tuple) or len(start_position) != 3:
            return False
        if not isinstance(target_position, tuple) or len(target_position) != 3:
            return False
        if speed <= 0:
            return False

        # Check if start position is inside any obstacle
        if self._is_inside_obstacle(start_position):
            return False

        # Check if target position is inside any obstacle
        if self._is_inside_obstacle(target_position):
            return False

        # Initialize space_state
        agent.space_state = {
            "position": start_position,
            "target": target_position,
            "speed": speed,
            "progress": 0.0,
            "path": path
        }

        # Track internally
        self._agent_position[agent] = start_position
        self._agent_target[agent] = target_position
        self._agent_speed[agent] = speed
        self._agent_path[agent] = path or []

        # If no path was provided, calculate an initial path using a simple algorithm
        if not path:
            calculated_path = self._calculate_path(start_position, target_position, agent)
            self._agent_path[agent] = calculated_path

        return True

    def add_obstacle(self, obstacle: Prism) -> None:
        """
        Add an obstacle to the space.
        """
        self._obstacles.append(obstacle)

    def remove_obstacle(self, obstacle: Prism) -> bool:
        """
        Remove an obstacle from the space.
        """
        if obstacle in self._obstacles:
            self._obstacles.remove(obstacle)
            return True
        return False

    def unregister(self, agent: BaseAgent) -> bool:
        """
        Unregister agent from space.
        """
        if agent not in self._agent_position:
            return False

        del self._agent_position[agent]
        del self._agent_target[agent]
        del self._agent_speed[agent]
        del self._agent_path[agent]

        agent.space_state = {}
        return True

    def update(self, delta_time: float) -> None:
        """
        Advance all agents by delta_time.
        Move agents toward target at constant speed avoiding obstacles.
        """
        for agent in list(self._agent_position.keys()):
            state = agent.space_state
            if not state:
                continue

            current_pos = self._agent_position[agent]
            target_pos = self._agent_target[agent]
            speed = self._agent_speed[agent]
            path = self._agent_path[agent]

            # If agent has a path, follow it; otherwise, move directly toward target
            if path and len(path) > 0:
                # Follow the path - move to the next waypoint in the path
                next_waypoint = path[0]
                
                # Compute direction to next waypoint
                dx = next_waypoint[0] - current_pos[0]
                dy = next_waypoint[1] - current_pos[1]
                dz = next_waypoint[2] - current_pos[2]

                distance_to_waypoint = (dx**2 + dy**2 + dz**2)**0.5
                if distance_to_waypoint <= 0:
                    # Reached this waypoint, remove it and continue to the next
                    path.pop(0)
                    continue

                # Distance to move this tick
                distance_to_move = speed * delta_time

                if distance_to_move >= distance_to_waypoint:
                    # Reach the waypoint
                    new_pos = next_waypoint
                    path.pop(0)  # Remove the reached waypoint
                else:
                    # Move partway toward the waypoint
                    ratio = distance_to_move / distance_to_waypoint
                    new_pos = (
                        current_pos[0] + dx * ratio,
                        current_pos[1] + dy * ratio,
                        current_pos[2] + dz * ratio
                    )
            else:
                # Move directly toward target
                dx = target_pos[0] - current_pos[0]
                dy = target_pos[1] - current_pos[1]
                dz = target_pos[2] - current_pos[2]

                distance_to_target = (dx**2 + dy**2 + dz**2)**0.5
                if distance_to_target <= 0:
                    state["progress"] = 1.0
                    continue

                # Distance to move this tick
                distance_to_move = speed * delta_time

                if distance_to_move >= distance_to_target:
                    # Reach target
                    new_pos = target_pos
                    state["progress"] = 1.0
                else:
                    # Move partway
                    ratio = distance_to_move / distance_to_target
                    new_pos = (
                        current_pos[0] + dx * ratio,
                        current_pos[1] + dy * ratio,
                        current_pos[2] + dz * ratio
                    )
                    # Update progress
                    total_distance = ((target_pos[0] - state["position"][0])**2 +
                                    (target_pos[1] - state["position"][1])**2 +
                                    (target_pos[2] - state["position"][2])**2)**0.5
                    if total_distance > 0:
                        traveled = ((new_pos[0] - state["position"][0])**2 +
                                  (new_pos[1] - state["position"][1])**2 +
                                  (new_pos[2] - state["position"][2])**2)**0.5
                        state["progress"] = min(1.0, state.get("progress", 0.0) + traveled / total_distance)

            # Update position
            self._agent_position[agent] = new_pos
            state["position"] = new_pos

    def get_state(self, agent: BaseAgent) -> Dict[str, Any]:
        """
        Get current space-specific state of agent.
        """
        if agent not in self._agent_position:
            return {}
        return agent.space_state.copy()

    def is_movement_complete(self, agent: BaseAgent) -> bool:
        """
        Check if agent has reached target.
        """
        state = agent.space_state
        if not state:
            return False
        return state.get("progress", 0.0) >= 1.0

    def _is_inside_obstacle(self, point: Point3D) -> bool:
        """
        Check if a point is inside any of the obstacles.
        """
        for obstacle in self._obstacles:
            base_points, height = obstacle
            if self._point_in_prism(point, base_points, height):
                return True
        return False

    def _point_in_prism(self, point: Point3D, base_points: List[Point3D], height: float) -> bool:
        """
        Check if a 3D point is inside a prism defined by base points and height.
        This is a simplified implementation for a prism that extends upward from the base.
        """
        px, py, pz = point
        
        # First, check if the Z coordinate is within the prism height
        # Assuming the base is in the XY plane, find Z bounds
        min_z = float('inf')
        max_z = float('-inf')
        for base_point in base_points:
            z_coord = base_point[2]
            min_z = min(min_z, z_coord)
            max_z = max(max_z, z_coord)
        
        # The prism extends from min_z to min_z + height
        if not (min_z <= pz <= min_z + height):
            return False
        
        # Check if point is inside the base polygon using ray casting
        x, y = px, py
        n = len(base_points)
        inside = False
        
        # Ray casting algorithm to check if point is inside polygon
        p1x, p1y = base_points[0][0], base_points[0][1]
        for i in range(1, n + 1):
            p2x, p2y = base_points[i % n][0], base_points[i % n][1]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside

    def _calculate_path(self, start: Point3D, target: Point3D, agent: BaseAgent) -> Path:
        """
        Calculate a path from start to target that avoids obstacles using a simple boundary following algorithm.
        If a straight line to the target intersects an obstacle, the agent will go around it.
        """
        # For a simple implementation, we'll just return the target directly
        # A more sophisticated implementation would implement the boundary following algorithm
        path = [target]
        
        # Check if the direct path intersects any obstacles
        if self._line_intersects_obstacle(start, target):
            # Implement simple boundary following here
            path = self._boundary_follow_path(start, target)
        
        return path

    def _boundary_follow_path(self, start: Point3D, target: Point3D) -> Path:
        """
        Simple boundary following algorithm.
        When a direct path hits an obstacle, the agent goes around the obstacle.
        This is a simplified implementation focused on 2D pathfinding with Z fixed.
        """
        # For now, just return the target as a simple fallback
        # In a more advanced implementation, we'd implement the actual boundary following
        path = [target]
        
        # Start with a direct path
        current = start
        path_points = [start]
        
        # Check if straight path to target intersects any obstacle
        while not self._is_direct_path_clear(current, target):
            # Find the first intersecting obstacle
            intersecting_obstacle = self._get_intersecting_obstacle(current, target)
            
            if intersecting_obstacle is None:
                break  # No more obstacles on path
                
            # Calculate a detour around this obstacle
            # For now, we'll just go above the obstacle in the Y direction
            base_points, height = intersecting_obstacle
            
            # Find the bounding box of the obstacle
            min_x = min(p[0] for p in base_points)
            max_x = max(p[0] for p in base_points)
            min_y = min(p[1] for p in base_points)
            max_y = max(p[1] for p in base_points)
            
            # Determine a point to go around the obstacle
            # Go above the obstacle
            detour_point = (max_x + 1, max_y + 2, current[2])
            
            # Add the detour point to the path
            path_points.append(detour_point)
            current = detour_point
            
            # Limit iterations to avoid infinite loops
            if len(path_points) > 20:
                break
        
        # Add target to the path
        path_points.append(target)
        
        return path_points[1:]  # Exclude the starting point

    def _is_direct_path_clear(self, start: Point3D, end: Point3D) -> bool:
        """
        Check if the direct path between two points is clear of obstacles.
        """
        return not self._line_intersects_obstacle(start, end)

    def _get_intersecting_obstacle(self, start: Point3D, end: Point3D) -> Optional[Prism]:
        """
        Return the first obstacle that intersects the line between start and end points.
        """
        for obstacle in self._obstacles:
            if self._line_intersects_prism(start, end, obstacle[0], obstacle[1]):
                return obstacle
        return None

    def _line_intersects_obstacle(self, p1: Point3D, p2: Point3D) -> bool:
        """
        Check if a line between two points intersects any obstacle.
        """
        for obstacle in self._obstacles:
            base_points, height = obstacle
            if self._line_intersects_prism(p1, p2, base_points, height):
                return True
        return False

    def _line_intersects_prism(self, p1: Point3D, p2: Point3D, base_points: List[Point3D], height: float) -> bool:
        """
        Check if a line intersects a prism (3D polygon extruded along Z-axis).
        This is a simplified implementation.
        """
        # Check if the line intersects the Z bounds of the prism
        min_z = float('inf')
        max_z = float('-inf')
        for base_point in base_points:
            z_coord = base_point[2]
            min_z = min(min_z, z_coord)
            max_z = max(max_z, z_coord)
        
        # The prism extends from min_z to min_z + height
        min_z_val = min_z
        max_z_val = min_z + height
        
        # Check if line segment crosses the Z range of the prism
        if not ((p1[2] <= max_z_val and p2[2] >= min_z_val) or (p2[2] <= max_z_val and p1[2] >= min_z_val)):
            return False
        
        # For simplicity, we'll check if the line passes through the base polygon 
        # at the average Z coordinate between p1 and p2
        avg_z = (p1[2] + p2[2]) / 2
        
        if not (min_z_val <= avg_z <= max_z_val):
            return False
        
        # Check if the line from p1 to p2 crosses the base polygon
        # This would require more complex 3D intersection calculations
        # For now, we'll simplify to 2D cross-section at the average Z level
        
        # Project the line onto the XY plane at average Z level
        # This is a simplification
        line_start = (p1[0], p1[1])
        line_end = (p2[0], p2[1])
        
        # Check if the line intersects the polygon at this Z level
        for i in range(len(base_points)):
            poly_start = (base_points[i][0], base_points[i][1])
            poly_end = (base_points[(i + 1) % len(base_points)][0], base_points[(i + 1) % len(base_points)][1])
            
            if self._lines_intersect(line_start, line_end, poly_start, poly_end):
                return True
        
        return False

    def _lines_intersect(self, p1: Tuple[float, float], p2: Tuple[float, float], 
                         p3: Tuple[float, float], p4: Tuple[float, float]) -> bool:
        """
        Check if two 2D line segments intersect.
        """
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4
        
        # Calculate the denominator
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-9:  # Lines are parallel
            return False
        
        # Calculate intersection parameters
        t_num = (x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)
        u_num = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3))
        
        t = t_num / den
        u = u_num / den
        
        # Check if intersection is within both line segments
        return 0 <= t <= 1 and 0 <= u <= 1



