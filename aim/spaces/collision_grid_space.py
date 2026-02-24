"""
Grid-based collision space with Spatial Hash optimization for fast obstacle lookup.

Uses clearance-expanded obstacles to automatically block narrow gaps.
2D grid with 4-connectivity (no diagonals).
"""

from typing import Dict, Any, List, Optional, Tuple
from aim.core.space import SpaceManager
from aim.core.agent import BaseAgent
import heapq

Point3D = Tuple[float, float, float]
GridPoint = Tuple[int, int, int]


class SpatialHashGrid:
    """
    Spatial hash for O(1) obstacle lookup.
    Obstacles are expanded by clearance to block narrow gaps.
    """

    def __init__(self, cell_size: float, clearance: float = 0.0):
        """
        :param cell_size: Size of each hash cell (matches grid resolution)
        :param clearance: Extra margin around obstacles (typically resolution / 2)
        """
        self.cell_size = cell_size
        self.clearance = clearance
        self.grid: Dict[int, Dict[int, List[Tuple[float, float, float, float]]]] = {}

    def _get_cell_key(self, x: float, y: float) -> Tuple[int, int]:
        """Get cell coordinates using floor division."""
        return (int(x // self.cell_size), int(y // self.cell_size))

    def add_obstacle(self, min_x: float, min_y: float, max_x: float, max_y: float):
        """Add obstacle to all cells it covers (expanded by clearance)."""
        exp_min_x = min_x - self.clearance
        exp_max_x = max_x + self.clearance
        exp_min_y = min_y - self.clearance
        exp_max_y = max_y + self.clearance

        min_cell_x = int(exp_min_x // self.cell_size)
        max_cell_x = int(exp_max_x // self.cell_size)
        min_cell_y = int(exp_min_y // self.cell_size)
        max_cell_y = int(exp_max_y // self.cell_size)

        for cx in range(min_cell_x, max_cell_x + 1):
            if cx not in self.grid:
                self.grid[cx] = {}
            for cy in range(min_cell_y, max_cell_y + 1):
                if cy not in self.grid[cx]:
                    self.grid[cx][cy] = []
                self.grid[cx][cy].append((exp_min_x, exp_max_x, exp_min_y, exp_max_y))

    def is_point_free(self, x: float, y: float) -> bool:
        """Check if point is free (only checks obstacles in same cell)."""
        cx, cy = self._get_cell_key(x, y)

        if cx not in self.grid or cy not in self.grid[cx]:
            return True

        for (obs_min_x, obs_max_x, obs_min_y, obs_max_y) in self.grid[cx][cy]:
            if obs_min_x <= x <= obs_max_x and obs_min_y <= y <= obs_max_y:
                return False

        return True


class CollisionGridSpace(SpaceManager):
    """
    2D grid-based space with collision avoidance.

    Grid points at regular intervals. Uses SpatialHashGrid with clearance
    to automatically block narrow gaps between obstacles.
    4-connectivity only (no diagonals).
    """

    def __init__(self,
                 boundaries: Tuple[Point3D, Point3D],
                 grid_resolution: float = 1.0,
                 obstacles: Optional[List[Tuple[List[Point3D], float]]] = None,
                 clearance_factor: float = 0.5):
        """
        :param boundaries: (min_point, max_point) defining space boundaries
        :param grid_resolution: Distance between adjacent grid points
        :param obstacles: List of (base_points, height) tuples
        :param clearance_factor: clearance = resolution * clearance_factor
        """
        self.min_bound, self.max_bound = boundaries
        self.grid_resolution = grid_resolution
        self.clearance = grid_resolution * clearance_factor
        self._obstacles = obstacles or []

        # 2D grid (single Z level)
        self.grid_size_x = int((self.max_bound[0] - self.min_bound[0]) / grid_resolution) + 2
        self.grid_size_y = int((self.max_bound[1] - self.min_bound[1]) / grid_resolution) + 2
        self.grid_size_z = 1

        # Build spatial hash
        self.spatial_hash = SpatialHashGrid(cell_size=grid_resolution, clearance=self.clearance)
        for base_points, height in self._obstacles:
            xs = [p[0] for p in base_points]
            ys = [p[1] for p in base_points]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            self.spatial_hash.add_obstacle(min_x, min_y, max_x, max_y)

        # Generate walkable grid
        self.grid: Dict[GridPoint, bool] = {}
        self._generate_grid()
        
        # Pre-compute neighbor cache for A* performance
        self._neighbor_cache: Dict[GridPoint, List[GridPoint]] = {}
        self._build_neighbor_cache()

        # Agent tracking
        self._agent_position: Dict[BaseAgent, Point3D] = {}
        self._agent_target: Dict[BaseAgent, Point3D] = {}
        self._agent_speed: Dict[BaseAgent, float] = {}
        self._agent_path: Dict[BaseAgent, List[Point3D]] = {}
    
    def _build_neighbor_cache(self):
        """Pre-compute walkable neighbors for each grid point. Called once during init."""
        for gx in range(self.grid_size_x):
            for gy in range(self.grid_size_y):
                gz = 0
                grid_point = (gx, gy, gz)
                if self.grid.get(grid_point, False):  # Only cache for walkable points
                    neighbors = []
                    # Check 4 directions
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = gx + dx, gy + dy
                        if 0 <= nx < self.grid_size_x and 0 <= ny < self.grid_size_y:
                            neighbor = (nx, ny, gz)
                            if self.grid.get(neighbor, False):
                                neighbors.append(neighbor)
                    self._neighbor_cache[grid_point] = neighbors

    def _generate_grid(self):
        """Generate 2D grid of walkable points."""
        gz = 0
        for gx in range(self.grid_size_x):
            for gy in range(self.grid_size_y):
                world_x = self.min_bound[0] + gx * self.grid_resolution
                world_y = self.min_bound[1] + gy * self.grid_resolution
                is_free = self.spatial_hash.is_point_free(world_x, world_y)
                self.grid[(gx, gy, gz)] = is_free

    def _world_to_grid(self, point: Point3D) -> Optional[GridPoint]:
        """Convert world coordinates to grid (rounds to nearest)."""
        x, y, z = point
        gx = round((x - self.min_bound[0]) / self.grid_resolution)
        gy = round((y - self.min_bound[1]) / self.grid_resolution)
        gz = 0

        if 0 <= gx < self.grid_size_x and 0 <= gy < self.grid_size_y:
            return (gx, gy, gz)
        return None

    def _grid_to_world(self, grid_point: GridPoint) -> Point3D:
        """Convert grid to world position."""
        gx, gy, gz = grid_point
        x = self.min_bound[0] + gx * self.grid_resolution
        y = self.min_bound[1] + gy * self.grid_resolution
        z = 0.0
        return (x, y, z)

    def _get_neighbors(self, grid_point: GridPoint) -> List[GridPoint]:
        """Get 4-connected walkable neighbors - uses pre-computed cache."""
        return self._neighbor_cache.get(grid_point, [])

    def _heuristic(self, a: GridPoint, b: GridPoint) -> float:
        """Manhattan distance heuristic."""
        return (abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])) * self.grid_resolution

    def _a_star(self, start: GridPoint, end: GridPoint) -> Optional[List[GridPoint]]:
        """A* pathfinding."""
        open_set = [(0, 0, start)]
        came_from: Dict[GridPoint, GridPoint] = {}
        g_score: Dict[GridPoint, float] = {start: 0}

        while open_set:
            _, current_g, current = heapq.heappop(open_set)

            if current == end:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]

            for neighbor in self._get_neighbors(current):
                tentative_g = current_g + self.grid_resolution
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f = tentative_g + self._heuristic(neighbor, end)
                    heapq.heappush(open_set, (f, tentative_g, neighbor))

        return None

    def register(self, agent: BaseAgent, initial_state: Dict[str, Any]) -> bool:
        """Register agent and calculate path."""
        start_position = initial_state.get("start_position")
        target_position = initial_state.get("target_position")
        speed = initial_state.get("speed", 1.0)
        path = initial_state.get("path")

        if not start_position or not target_position:
            return False
        if speed <= 0:
            return False

        start_grid = self._world_to_grid(start_position)
        target_grid = self._world_to_grid(target_position)

        if not start_grid or not target_grid:
            return False
        if not self.grid.get(start_grid, False) or not self.grid.get(target_grid, False):
            return False

        agent.space_state = {
            "position": start_position,
            "target": target_position,
            "speed": speed,
            "progress": 0.0,
            "path": path
        }

        self._agent_position[agent] = start_position
        self._agent_target[agent] = target_position
        self._agent_speed[agent] = speed

        if path is None:
            grid_path = self._a_star(start_grid, target_grid)
            if grid_path:
                world_path = [self._grid_to_world(gp) for gp in grid_path]
                world_path.append(target_position)
                self._agent_path[agent] = world_path
            else:
                self._agent_path[agent] = []
        else:
            self._agent_path[agent] = path[:]

        return True

    def unregister(self, agent: BaseAgent) -> bool:
        """Unregister agent."""
        if agent not in self._agent_position:
            return False
        del self._agent_position[agent]
        del self._agent_target[agent]
        del self._agent_speed[agent]
        del self._agent_path[agent]
        agent.space_state = {}
        return True

    def update(self, delta_time: float) -> None:
        """Advance agents along paths."""
        for agent in list(self._agent_position.keys()):
            state = agent.space_state
            if not state:
                continue

            current_pos = self._agent_position[agent]
            target_pos = self._agent_target[agent]
            speed = self._agent_speed[agent]
            path = self._agent_path[agent]

            if path and len(path) > 0:
                next_waypoint = path[0]
                dx = next_waypoint[0] - current_pos[0]
                dy = next_waypoint[1] - current_pos[1]
                dz = next_waypoint[2] - current_pos[2]
                dist = (abs(dx) + abs(dy) + abs(dz))

                if dist <= 0.01:
                    path.pop(0)
                    if not path:
                        state["progress"] = 1.0
                        current_pos = target_pos
                    else:
                        current_pos = current_pos
                else:
                    move_dist = speed * delta_time
                    if move_dist >= dist:
                        current_pos = next_waypoint
                        path.pop(0)
                    else:
                        ratio = move_dist / dist
                        current_pos = (
                            current_pos[0] + dx * ratio,
                            current_pos[1] + dy * ratio,
                            current_pos[2] + dz * ratio
                        )
            else:
                dx = target_pos[0] - current_pos[0]
                dy = target_pos[1] - current_pos[1]
                dz = target_pos[2] - current_pos[2]
                dist = (dx**2 + dy**2 + dz**2)**0.5
                if dist <= 0.01:
                    state["progress"] = 1.0
                current_pos = current_pos

            self._agent_position[agent] = current_pos
            state["position"] = current_pos

    def get_state(self, agent: BaseAgent) -> Dict[str, Any]:
        """Get agent space state."""
        if agent not in self._agent_position:
            return {}
        return agent.space_state.copy()

    def is_movement_complete(self, agent: BaseAgent) -> bool:
        """Check if agent reached target."""
        state = agent.space_state
        return state.get("progress", 0.0) >= 1.0 if state else False
