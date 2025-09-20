import heapq
import sys
from typing import Dict, Any, List, Optional, Set, Tuple

from aim.core.space import SpaceManager
from aim.core.agent import BaseAgent
from aim.entities.manufacturing.conveyor import Conveyor
from aim.entities.manufacturing.turn_table import TurnTable


class ConveyorSpace(SpaceManager):
    """
    Manages agents moving on a graph of conveyors, turntables, and other spatial entities.
    Handles movement, collision detection, and path progression.
    """

    def __init__(self):
        # Agent -> current entity (Conveyor, TurnTable, etc.)
        self._agent_entity: Dict[BaseAgent, Any] = {}
        # Entity -> set of agents on it (for collision detection)
        self._entity_agents: Dict[Any, Set[BaseAgent]] = {}

    def register_entity(self, entity: Any) -> None:
        if entity not in self._entity_agents:
            self._entity_agents[entity] = set()

    def is_entity_registered(self, entity: Any) -> bool:
        return entity in self._entity_agents

    def _compute_entity_time(self, entity: Any) -> float:
        """Compute time to traverse entity. Returns inf if invalid."""
        if isinstance(entity, Conveyor):
            length = entity.get_total_length()
            if length <= 0 or entity.speed <= 0:
                return float('inf')
            return length / entity.speed
        elif isinstance(entity, TurnTable):
            # Assume full rotation if no target_angle
            if not hasattr(entity, 'angular_speed') or entity.angular_speed <= 0:
                return float('inf')
            # For now, assume 2*pi radians for full turn
            return 6.28318530718 / entity.angular_speed
        else:
            # Unknown entity — assume 1.0 time unit
            return 1.0

    def _find_shortest_path(self, start: Any, end: Any) -> Optional[List[Any]]:
        """
        Find shortest-time path from start to end using Dijkstra's algorithm.
        Returns list of entities from start to end, or None if no path.
        """
        if start == end:
            return [start]

        # Priority queue: (time, entity, path)
        pq = [(0.0, start, [start])]
        visited = set()

        while pq:
            current_time, current_entity, path = heapq.heappop(pq)

            if current_entity in visited:
                continue
            visited.add(current_entity)

            if not hasattr(current_entity, 'connections'):
                continue

            for neighbor in current_entity.connections:
                if neighbor in visited:
                    continue

                edge_time = self._compute_entity_time(neighbor)
                if edge_time == float('inf'):
                    continue

                new_time = current_time + edge_time
                new_path = path + [neighbor]

                if neighbor == end:
                    return new_path

                heapq.heappush(pq, (new_time, neighbor, new_path))

        return None

    def register(self, agent: BaseAgent, initial_state: Dict[str, Any]) -> bool:
        # print(f"[SPACE] Registering agent {id(agent)} from {initial_state.get('start_entity')} to {initial_state.get('end_entity')}")
        start_entity = initial_state.get("start_entity")
        end_entity = initial_state.get("end_entity")

        if start_entity is None or end_entity is None:
            print("[SPACE] Missing start or end entity")
            return False

        if not self.is_entity_registered(start_entity) or not self.is_entity_registered(end_entity):
            print("[SPACE] Entity not registered")
            return False

        path = self._find_shortest_path(start_entity, end_entity)
        if path is None:
            print(f"[SPACE] NO PATH FOUND from {start_entity} to {end_entity}")
            sys.exit(1)  # You should see this if no path
        # print(f"[SPACE] Path found: {[getattr(e, 'name', str(e)) for e in path]}")

        # Compute total time for path
        total_time = 0.0
        for entity in path:
            total_time += self._compute_entity_time(entity)

        if total_time <= 0:
            total_time = 1.0  # Avoid division by zero

        # Initialize space_state
        agent.space_state = {
            "entity": start_entity,
            "path": path,
            "progress_on_entity": 0.0,
            "progress_on_path": 0.0,
            "target_entity": end_entity,
            "total_time": total_time,
            "elapsed_time": 0.0,
            "elapsed_time_on_entity": 0.0
        }

        # Check collision on start_entity only
        if not self._can_place_agent(agent, start_entity):
            agent.space_state = {}
            return False

        # Assign to entity
        self._agent_entity[agent] = start_entity
        self._entity_agents[start_entity].add(agent)

        return True

    def unregister(self, agent: BaseAgent) -> bool:
        if agent not in self._agent_entity:
            return False

        entity = self._agent_entity[agent]
        self._entity_agents[entity].discard(agent)

        # Clear agent's space_state
        agent.space_state = {}

        del self._agent_entity[agent]

        return True

    def update(self, delta_time: float) -> None:
        for agent in list(self._agent_entity.keys()):
            state = agent.space_state
            if not state:
                continue

            current_entity = state["entity"]
            entity_time = self._compute_entity_time(current_entity)

            # Update time on current entity
            state["elapsed_time_on_entity"] += delta_time
            state["elapsed_time"] += delta_time

            # Update progress on current entity
            if entity_time > 0:
                progress_on_entity = state["elapsed_time_on_entity"] / entity_time
                state["progress_on_entity"] = min(1.0, progress_on_entity)
            else:
                state["progress_on_entity"] = 1.0

            # Update progress on path
            if state["total_time"] > 0:
                state["progress_on_path"] = min(1.0, state["elapsed_time"] / state["total_time"])
            else:
                state["progress_on_path"] = 1.0

            # Check if need to move to next entity
            if state["progress_on_entity"] >= 1.0:
                path = state["path"]
                if len(path) > 1:
                    # Move to next entity
                    next_entity = path[1]
                    state["entity"] = next_entity
                    state["path"] = path[1:]
                    state["elapsed_time_on_entity"] = 0.0  # Reset for new entity
                    state["progress_on_entity"] = 0.0  # Reset for new entity
                    # Reassign in space
                    old_entity = self._agent_entity[agent]
                    self._entity_agents[old_entity].discard(agent)
                    self._agent_entity[agent] = next_entity
                    if next_entity not in self._entity_agents:
                        self._entity_agents[next_entity] = set()
                    self._entity_agents[next_entity].add(agent)
                else:
                    # End of path — do nothing, agent will be ejected when progress_on_path=1.0
                    pass

    def get_state(self, agent: BaseAgent) -> Dict[str, Any]:
        return agent.space_state.copy()

    def is_movement_complete(self, agent: BaseAgent) -> bool:
        state = agent.space_state
        if not state:
            return False
        return state.get("progress_on_path", 0.0) >= 1.0

    def _can_place_agent(self, agent: BaseAgent, entity: Any) -> bool:
        if entity not in self._entity_agents:
            return True

        if isinstance(entity, Conveyor):
            total_length = entity.get_total_length()
            if total_length == 0:
                return False
            required_progress = agent.length / total_length

            for other_agent in self._entity_agents[entity]:
                other_state = other_agent.space_state
                if not other_state:
                    continue
                other_start = other_state["progress_on_entity"] - other_agent.length / total_length
                other_end = other_state["progress_on_entity"]
                if other_start < required_progress and other_end > 0.0:
                    return False

        return True
