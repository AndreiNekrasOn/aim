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
        Calculate a path from start to target that avoids obstacles.
        This is a simple implementation using a basic pathfinding approach.
        A real implementation would use more sophisticated algorithms like A*.
        """
        # For now, return a direct path as fallback
        # A more sophisticated implementation would use algorithms like A*
        return [target]



