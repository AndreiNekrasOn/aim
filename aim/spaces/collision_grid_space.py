"""
Grid-based collision space implementation with A* pathfinding and Spatial Hash optimization.
"""

from typing import Dict, Any, List, Optional, Set, Tuple, DefaultDict
from aim.core.space import SpaceManager
from aim.core.agent import BaseAgent
import heapq
from collections import defaultdict, deque

Point3D = Tuple[float, float, float]
GridPoint = Tuple[int, int, int]


class SpatialHash:
    """
    Пространственное индексирование для быстрой проверки принадлежности точки к препятствию.
    Разбивает пространство на регионы, хранит list obstacles для каждого региона.
    Работает в 2D (XY плоскость).
    """
    
    def __init__(self, cell_size: float = 2.0):
        """
        :param cell_size: Размер региона в метрах. Должен быть больше типичного obstacle.
        """
        self.cell_size = cell_size
        self.regions: DefaultDict[Tuple[int, int], List[Tuple[Tuple[Point3D, ...], float, Tuple[float, float, float, float]]]] = defaultdict(list)
    
    def add(self, base_points: List[Point3D], height: float):
        """Добавляет obstacle во все регионы которые он пересекает."""
        # Вычисляем 2D bounding box obstacle (только XY)
        min_x = min(p[0] for p in base_points)
        max_x = max(p[0] for p in base_points)
        min_y = min(p[1] for p in base_points)
        max_y = max(p[1] for p in base_points)
        
        # Определяем регионы которые пересекает obstacle
        min_rx = int(min_x / self.cell_size)
        max_rx = int(max_x / self.cell_size)
        min_ry = int(min_y / self.cell_size)
        max_ry = int(max_y / self.cell_size)
        
        # Кэшируем 2D bounding box для быстрой проверки
        xy_bounds = (min_x, max_x, min_y, max_y)
        
        # Добавляем obstacle во все пересекаемые регионы
        obstacle = (tuple(base_points), height, xy_bounds)
        for rx in range(min_rx, max_rx + 1):
            for ry in range(min_ry, max_ry + 1):
                self.regions[(rx, ry)].append(obstacle)
    
    def query(self, x: float, y: float) -> List[Tuple[Tuple[Point3D, ...], float, Tuple[float, float, float, float]]]:
        """
        Возвращает obstacles которые содержат точку (x, y) в XY плоскости.
        Проверяет только obstacles в регионе точки + точная проверка.
        """
        rx, ry = int(x / self.cell_size), int(y / self.cell_size)
        candidates = self.regions.get((rx, ry), [])
        
        # Быстрая отсечка по bounding box перед точной проверкой
        result = []
        for obs in candidates:
            _, _, xy_bounds = obs
            min_x, max_x, min_y, max_y = xy_bounds
            
            # Быстрая проверка bounding box
            if not (min_x <= x <= max_x and min_y <= y <= max_y):
                continue
            
            # Точная проверка (только XY, игнорируем Z)
            if self._point_in_polygon((x, y), obs[0]):
                result.append(obs)
        
        return result
    
    def _point_in_polygon(self, point: Tuple[float, float], base_points: Tuple[Point3D, ...]) -> bool:
        """Check if a 2D point is inside a polygon using ray casting."""
        px, py = point
        n = len(base_points)
        inside = False
        
        p1x, p1y = base_points[0][0], base_points[0][1]
        for i in range(1, n + 1):
            p2x, p2y = base_points[i % n][0], base_points[i % n][1]
            if py > min(p1y, p2y):
                if py <= max(p1y, p2y):
                    if px <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (py - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or px <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside


class CollisionGridSpace(SpaceManager):
    """
    Manages agents moving in 3D space with collisions and obstacles using a grid-based approach.
    Creates a grid of walkable points and uses A* for pathfinding within the grid.

    Uses Spatial Hash for O(1) obstacle lookup instead of O(n) for each grid cell.
    """

    def __init__(self,
                 boundaries: Tuple[Point3D, Point3D],  # (min_point, max_point)
                 grid_resolution: float = 1.0,
                 obstacles: Optional[List[Tuple[List[Point3D], float]]] = None,
                 spatial_hash_cell_size: float = 2.0):
        """
        Initialize grid space with boundaries and obstacles.

        :param boundaries: Tuple of (min_point, max_point) defining the 3D space boundaries
        :param grid_resolution: Size of each grid cell
        :param obstacles: List of obstacles, each obstacle is (base_points, height) tuple
        :param spatial_hash_cell_size: Size of spatial hash regions (should be > typical obstacle size)
        """
        self.min_bound, self.max_bound = boundaries
        self.grid_resolution = grid_resolution
        self._obstacles = obstacles or []

        # Calculate grid dimensions
        self.grid_size_x = int((self.max_bound[0] - self.min_bound[0]) / grid_resolution) + 1
        self.grid_size_y = int((self.max_bound[1] - self.min_bound[1]) / grid_resolution) + 1
        self.grid_size_z = int((self.max_bound[2] - self.min_bound[2]) / grid_resolution) + 1

        # Create grid to mark occupied cells (True = walkable, False = blocked)
        # Default is walkable
        self.grid: Dict[GridPoint, bool] = {}

        # Build spatial hash for fast obstacle lookup
        self.spatial_hash = SpatialHash(cell_size=spatial_hash_cell_size)
        for base_points, height in self._obstacles:
            self.spatial_hash.add(base_points, height)

        # Generate walkable grid points and connections
        self._generate_grid()

        # Agent tracking
        self._agent_position: Dict[BaseAgent, Point3D] = {}
        self._agent_target: Dict[BaseAgent, Point3D] = {}
        self._agent_speed: Dict[BaseAgent, float] = {}
        self._agent_path: Dict[BaseAgent, List[Point3D]] = {}  # Current path being followed

    def _generate_grid(self):
        """
        Generate the grid of walkable points using Spatial Hash.
        
        Complexity: O(grid_cells × k) where k = avg obstacles per region (~5-10)
        vs O(grid_cells × n) where n = total obstacles (6500+)
        
        For 14000 cells × 5 candidates = 70K checks vs 1.3B checks (~18000x faster)
        """
        # Iterate through all grid cells (only XY, Z is fixed)
        for gx in range(self.grid_size_x):
            for gy in range(self.grid_size_y):
                # Check all 4 corners of the cell
                cell_blocked = False
                for dx in [0.0, 1.0]:
                    for dy in [0.0, 1.0]:
                        world_x = self.min_bound[0] + (gx + dx) * self.grid_resolution
                        world_y = self.min_bound[1] + (gy + dy) * self.grid_resolution
                        
                        # Query spatial hash for obstacles at this corner (2D only)
                        blocking_obstacles = self.spatial_hash.query(world_x, world_y)
                        
                        if blocking_obstacles:
                            cell_blocked = True
                            break
                    if cell_blocked:
                        break
                
                # Mark all Z levels based on whether ANY corner is blocked
                for gz in range(self.grid_size_z):
                    self.grid[(gx, gy, gz)] = not cell_blocked

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
        """Get all valid walkable neighbors."""
        gx, gy, gz = grid_point
        neighbors = []

        # X-direction neighbors
        for dx in [-1, 1]:
            new_gx = gx + dx
            if 0 <= new_gx < self.grid_size_x:
                neighbor_pos = (new_gx, gy, gz)
                if self.grid.get(neighbor_pos, True):
                    neighbors.append(neighbor_pos)

        # Y-direction neighbors
        for dy in [-1, 1]:
            new_gy = gy + dy
            if 0 <= new_gy < self.grid_size_y:
                neighbor_pos = (gx, new_gy, gz)
                if self.grid.get(neighbor_pos, True):
                    neighbors.append(neighbor_pos)

        return neighbors

    def _edge_is_clear(self, from_grid: GridPoint, to_grid: GridPoint, samples: int = 3) -> bool:
        """
        Проверяет что ребро между двумя точками не пересекает препятствия.
        В текущей реализации не используется (упрощено до проверки соседних ячеек).
        """
        return True  # Упрощение: проверяем только ячейки, не рёбра

    def _heuristic(self, a: GridPoint, b: GridPoint) -> float:
        """Calculate heuristic distance between two grid points (Manhattan distance)."""
        return (abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])) * self.grid_resolution

    def _a_star(self, start_grid: GridPoint, end_grid: GridPoint) -> Optional[List[GridPoint]]:
        """A* pathfinding algorithm on the grid."""
        # Priority queue: (f_score, g_score, grid_point)
        open_set = [(0, 0, start_grid)]
        came_from: Dict[GridPoint, GridPoint] = {}
        g_score: Dict[GridPoint, float] = {start_grid: 0}

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
                tentative_g_score = current_g + self.grid_resolution

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score = tentative_g_score + self._heuristic(neighbor, end_grid)
                    heapq.heappush(open_set, (f_score, tentative_g_score, neighbor))

        return None  # No path found

    def _is_within_boundaries(self, point: Point3D) -> bool:
        """Check if a point is within the defined boundaries."""
        x, y, z = point
        min_x, min_y, min_z = self.min_bound
        max_x, max_y, max_z = self.max_bound
        return min_x <= x <= max_x and min_y <= y <= max_y and min_z <= z <= max_z

    def _find_closest_walkable_grid(self, world_point: Point3D) -> Optional[GridPoint]:
        """Find the closest walkable grid point to a world point using BFS."""
        initial_grid = self._world_to_grid(world_point)

        if initial_grid is None:
            return None

        # If the initial grid point is walkable, return it
        if self.grid.get(initial_grid, True):
            return initial_grid

        # Otherwise, search in increasing distances using BFS
        queue = deque([initial_grid])
        visited: Set[GridPoint] = {initial_grid}

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
            print(f"  register FAILED: no start/target")
            return False

        if not isinstance(start_position, tuple) or len(start_position) != 3:
            print(f"  register FAILED: invalid start_position")
            return False
        if not isinstance(target_position, tuple) or len(target_position) != 3:
            print(f"  register FAILED: invalid target_position")
            return False
        if speed <= 0:
            print(f"  register FAILED: invalid speed {speed}")
            return False

        # Check if start and target positions are within bounds
        if (not self._is_within_boundaries(start_position) or
            not self._is_within_boundaries(target_position)):
            print(f"  register FAILED: out of bounds")
            return False

        # Check if start and target positions are not inside obstacles
        start_grid = self._world_to_grid(start_position)
        target_grid = self._world_to_grid(target_position)

        if start_grid is None or not self.grid.get(start_grid, True):
            print(f"  register FAILED: start inside obstacle, grid={start_grid}")
            return False
        if target_grid is None or not self.grid.get(target_grid, True):
            print(f"  register FAILED: target inside obstacle, grid={target_grid}")
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
            
            print(f"  register: start_grid={start_grid}, target_grid={target_grid}")

            if start_grid is not None and target_grid is not None:
                # Calculate path using A*
                grid_path = self._a_star(start_grid, target_grid)
                
                print(f"  register: grid_path length={len(grid_path) if grid_path else 'None'}")

                if grid_path is not None:
                    # Convert grid path to world coordinates
                    world_path = [self._grid_to_world(gp) for gp in grid_path]
                    # Add the actual target position at the end
                    world_path.append(target_position)
                    self._agent_path[agent] = world_path
                    print(f"  register: SUCCESS, world_path length={len(world_path)}")
                else:
                    # No path found, set empty path
                    self._agent_path[agent] = []
                    print(f"  register: NO PATH FOUND")
            else:
                # No close walkable points found
                self._agent_path[agent] = []
                print(f"  register: NO WALKABLE GRID")
        else:
            # Use provided path
            self._agent_path[agent] = path[:]
            print(f"  register: SUCCESS (using provided path)")

        return True

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
                # No path available - agent is stuck or at target
                # Check if already at target
                dx = target_pos[0] - current_pos[0]
                dy = target_pos[1] - current_pos[1]
                dz = target_pos[2] - current_pos[2]
                distance_to_target = (dx**2 + dy**2 + dz**2)**0.5
                
                if distance_to_target <= 0.01:  # Already at target
                    state["progress"] = 1.0
                    new_pos = target_pos
                else:
                    # No path and not at target - agent cannot move
                    # This happens when target is unreachable (inside obstacle or no path exists)
                    new_pos = current_pos
                    # Don't update progress - agent is stuck

            # COLLISION CHECK: Verify new position is not inside an obstacle
            obstacles_at_new_pos = self.spatial_hash.query(new_pos[0], new_pos[1])
            if obstacles_at_new_pos:
                raise RuntimeError(
                    f"Agent collision detected at ({new_pos[0]:.2f}, {new_pos[1]:.2f})! "
                    f"Agent is inside {len(obstacles_at_new_pos)} obstacle(s). "
                    f"This indicates a pathfinding bug."
                )

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
