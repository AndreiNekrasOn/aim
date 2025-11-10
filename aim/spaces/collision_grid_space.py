"""
Grid-based collision space implementation with A* pathfinding
"""

from typing import Dict, Any, List, Optional, Set, Tuple, Deque
from aim.core.space import SpaceManager
from aim.core.agent import BaseAgent
import heapq
from tqdm import tqdm

Point3D = Tuple[float, float, float]
GridPoint = Tuple[int, int, int]

class CollisionGridSpace(SpaceManager):
    """
    Manages agents moving in 3D space with collisions and obstacles using a grid-based approach.
    Creates a grid of walkable points and uses A* for pathfinding within the grid.
    """

    def __init__(self,
                 boundaries: Tuple[Point3D, Point3D],  # (min_point, max_point)
                 grid_resolution: float = 1.0,
                 obstacles: Optional[List[Tuple[List[Point3D], float]]] = None):
        """
        Initialize grid space with boundaries and obstacles.

        :param boundaries: Tuple of (min_point, max_point) defining the 3D space boundaries
        :param grid_resolution: Size of each grid cell
        :param obstacles: List of obstacles, each obstacle is (base_points, height) tuple
        """
        self.min_bound, self.max_bound = boundaries
        self.grid_resolution = grid_resolution
        self._obstacles = obstacles or []

        # Calculate grid dimensions
        self.grid_size_x = int((self.max_bound[0] - self.min_bound[0]) / grid_resolution) + 1
        self.grid_size_y = int((self.max_bound[1] - self.min_bound[1]) / grid_resolution) + 1
        self.grid_size_z = int((self.max_bound[2] - self.min_bound[2]) / grid_resolution) + 1

        # Create grid to mark occupied cells
        self.grid = {}

        # Generate walkable grid points and connections
        self._generate_grid()

        # Agent tracking
        self._agent_position: Dict[BaseAgent, Point3D] = {}
        self._agent_target: Dict[BaseAgent, Point3D] = {}
        self._agent_speed: Dict[BaseAgent, float] = {}
        self._agent_path: Dict[BaseAgent, List[Point3D]] = {}  # Current path being followed

    def _generate_grid(self):
        """Generate the grid of walkable points and connections."""
        # Mark obstacle cells as occupied
        for i, (base_points, height) in enumerate(tqdm(self._obstacles, desc="Processing obstacles", leave=False)):
            self._mark_obstacle_cells(base_points, height)

    def _mark_obstacle_cells(self, base_points: List[Point3D], height: float):
        """Mark all cells occupied by an obstacle."""
        # For each point in the obstacle volume, mark the corresponding grid cell
        for x in range(self.grid_size_x):
            for y in range(self.grid_size_y):
                for z in range(self.grid_size_z):
                    # Convert grid coordinates to world coordinates
                    world_x = self.min_bound[0] + x * self.grid_resolution
                    world_y = self.min_bound[1] + y * self.grid_resolution
                    world_z = self.min_bound[2] + z * self.grid_resolution

                    # Check if this point is inside the obstacle
                    if self._is_point_in_prism((world_x, world_y, world_z), base_points, height):
                        # Mark this grid cell as occupied
                        self.grid[(x, y, z)] = False  # Not walkable

    def _is_point_in_prism(self, point: Point3D, base_points: List[Point3D], height: float) -> bool:
        """Check if a 3D point is inside a prism defined by base points and height."""
        px, py, pz = point

        # Check Z range
        min_z = min(p[2] for p in base_points)
        max_z = min_z + height
        if not (min_z <= pz <= max_z):
            return False

        # Check if point is inside the base polygon (XY projection)
        x, y = px, py
        n = len(base_points)
        inside = False

        # Ray casting algorithm
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

    def _world_to_grid(self, point: Point3D) -> Optional[GridPoint]:
        """Convert world coordinates to grid coordinates."""
        x, y, z = point
        grid_x = int((x - self.min_bound[0]) / self.grid_resolution)
        grid_y = int((y - self.min_bound[1]) / self.grid_resolution)
        grid_z = int((z - self.min_bound[2]) / self.grid_resolution)

        # Check if within bounds
        if (0 <= grid_x < self.grid_size_x and
            0 <= grid_y < self.grid_size_y and
            0 <= grid_z < self.grid_size_z):
            return (grid_x, grid_y, grid_z)
        return None

    def _grid_to_world(self, grid_point: GridPoint) -> Point3D:
        """Convert grid coordinates to world coordinates."""
        gx, gy, gz = grid_point
        x = self.min_bound[0] + gx * self.grid_resolution + self.grid_resolution / 2
        y = self.min_bound[1] + gy * self.grid_resolution + self.grid_resolution / 2
        z = self.min_bound[2] + gz * self.grid_resolution + self.grid_resolution / 2
        return (x, y, z)

    def _get_neighbors(self, grid_point: GridPoint) -> List[GridPoint]:
        """Get all valid neighbors of a grid point."""
        gx, gy, gz = grid_point
        neighbors = []

        # 4-connectivity in XY plane only (closest vertical/horizontal neighbors, no diagonals)
        # X-direction neighbors
        for dx in [-1, 1]:
            new_gx = gx + dx
            if 0 <= new_gx < self.grid_size_x:
                neighbor_pos = (new_gx, gy, gz)
                if self.grid.get(neighbor_pos, True):  # True means walkable by default
                    neighbors.append(neighbor_pos)

        # Y-direction neighbors
        for dy in [-1, 1]:
            new_gy = gy + dy
            if 0 <= new_gy < self.grid_size_y:
                neighbor_pos = (gx, new_gy, gz)
                if self.grid.get(neighbor_pos, True):  # True means walkable by default
                    neighbors.append(neighbor_pos)

        return neighbors

    def _heuristic(self, a: GridPoint, b: GridPoint) -> float:
        """Calculate heuristic distance between two grid points (Manhattan distance)."""
        return (abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])) * self.grid_resolution

    def _a_star(self, start_grid: GridPoint, end_grid: GridPoint) -> Optional[List[GridPoint]]:
        """A* pathfinding algorithm on the grid."""
        # Priority queue: (f_score, g_score, grid_point)
        open_set = [(0, 0, start_grid)]
        came_from = {}
        g_score = {start_grid: 0}

        while open_set:
            current_f, current_g, current = heapq.heappop(open_set)

            if current == end_grid:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start_grid)
                return path[::-1]  # Reverse to get path from start to end

            for neighbor in self._get_neighbors(current):
                tentative_g_score = current_g + self.grid_resolution  # Assuming unit cost for all neighbors

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score = tentative_g_score + self._heuristic(neighbor, end_grid)
                    heapq.heappush(open_set, (f_score, tentative_g_score, neighbor))

        return None  # No path found

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

        # Check if start and target positions are within bounds
        if (not self._is_within_boundaries(start_position) or
            not self._is_within_boundaries(target_position)):
            return False

        # Check if start and target positions are not inside obstacles
        start_grid = self._world_to_grid(start_position)
        target_grid = self._world_to_grid(target_position)

        if start_grid is None or not self.grid.get(start_grid, True):
            return False
        if target_grid is None or not self.grid.get(target_grid, True):
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

        # Calculate path if not provided
        if path is None:
            # Find closest grid points to start and target
            start_grid = self._find_closest_walkable_grid(start_position)
            target_grid = self._find_closest_walkable_grid(target_position)

            if start_grid is not None and target_grid is not None:
                # Calculate path using A*
                grid_path = self._a_star(start_grid, target_grid)

                if grid_path is not None:
                    # Convert grid path to world coordinates
                    world_path = [self._grid_to_world(gp) for gp in grid_path]
                    # Add the actual target position at the end
                    world_path.append(target_position)
                    self._agent_path[agent] = world_path
                else:
                    # No path found, set empty path
                    self._agent_path[agent] = []
            else:
                # No close walkable points found
                self._agent_path[agent] = []
        else:
            # Use provided path
            self._agent_path[agent] = path[:]

        return True

    def _is_within_boundaries(self, point: Point3D) -> bool:
        """Check if a point is within the defined boundaries."""
        x, y, z = point
        min_x, min_y, min_z = self.min_bound
        max_x, max_y, max_z = self.max_bound
        return min_x <= x <= max_x and min_y <= y <= max_y and min_z <= z <= max_z

    def _find_closest_walkable_grid(self, world_point: Point3D) -> Optional[GridPoint]:
        """Find the closest walkable grid point to a world point."""
        initial_grid = self._world_to_grid(world_point)

        if initial_grid is None:
            return None

        # If the initial grid point is walkable, return it
        if self.grid.get(initial_grid, True):
            return initial_grid

        # Otherwise, search in increasing distances using BFS
        from collections import deque
        queue = deque([initial_grid])
        visited = {initial_grid}

        while queue:
            grid_point = queue.popleft()

            # Check if this point is walkable
            if self.grid.get(grid_point, True):
                return grid_point

            # Add neighbors to queue
            for neighbor in self._get_neighbors(grid_point):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return None  # No walkable point found

    def unregister(self, agent: BaseAgent) -> bool:
        """Unregister agent from space."""
        if agent not in self._agent_position:
            return False

        del self._agent_position[agent]
        del self._agent_target[agent]
        del self._agent_speed[agent]
        del self._agent_path[agent]

        agent.space_state = {}
        return True

    def update(self, delta_time: float) -> None:
        """Advance all agents by delta_time."""
        for agent in list(self._agent_position.keys()):
            state = agent.space_state
            if not state:
                continue

            current_pos = self._agent_position[agent]
            target_pos = self._agent_target[agent]
            speed = self._agent_speed[agent]
            path = self._agent_path[agent]

            # If we have a specific path to follow
            if path and len(path) > 0:
                # Follow the path - move to the next waypoint in the path
                next_waypoint = path[0]

                # Compute direction to next waypoint
                dx = next_waypoint[0] - current_pos[0]
                dy = next_waypoint[1] - current_pos[1]
                dz = next_waypoint[2] - current_pos[2]

                distance_to_waypoint = (dx**2 + dy**2 + dz**2)**0.5
                if distance_to_waypoint <= 0.01:  # Close enough to waypoint
                    # Reached this waypoint, remove it and continue to the next
                    path.pop(0)
                    if len(path) == 0:
                        # Finished the path, set to target
                        new_pos = target_pos
                        state["progress"] = 1.0
                    else:
                        # Move to the next waypoint in the next call
                        new_pos = current_pos
                else:
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
                # Move directly toward target (may be outside grid area)
                dx = target_pos[0] - current_pos[0]
                dy = target_pos[1] - current_pos[1]
                dz = target_pos[2] - current_pos[2]

                distance_to_target = (dx**2 + dy**2 + dz**2)**0.5
                if distance_to_target <= 0.01:  # Close enough to target
                    state["progress"] = 1.0
                    new_pos = target_pos
                else:
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
        """Get current space-specific state of agent."""
        if agent not in self._agent_position:
            return {}
        return agent.space_state.copy()

    def is_movement_complete(self, agent: BaseAgent) -> bool:
        """Check if agent has reached target."""
        state = agent.space_state
        if not state:
            return False
        return state.get("progress", 0.0) >= 1.0