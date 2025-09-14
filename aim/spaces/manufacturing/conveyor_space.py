# spaces/manufacturing/conveyor_space.py

from typing import Dict, Any, List, Optional, Set
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
        # Agent -> movement state (progress, angle, target, etc.)
        self._agent_movement: Dict[BaseAgent, Dict[str, Any]] = {}
        # Entity -> set of agents on it (for collision detection)
        self._entity_agents: Dict[Any, Set[BaseAgent]] = {}
        # Set of all registered spatial entities (Conveyor, TurnTable, etc.)

    def register_entity(self, entity: Any) -> None:
        """
        Register a spatial entity (Conveyor, TurnTable, etc.) with this space.
        Ensures the entity is tracked for agent placement and collision detection.
        Safe to call multiple times — idempotent.
        """
        if entity not in self._entity_agents:
            self._entity_agents[entity] = set()

    def is_entity_registered(self, entity: Any) -> bool:
        """
        Check if a spatial entity is registered with this space.
        """
        return entity in self._entity_agents

    def register(self, agent: BaseAgent, initial_state: Dict[str, Any]) -> bool:
        start_entity = initial_state.get("start_entity")
        if start_entity is None:
            return False

        if not self.is_entity_registered(start_entity):
            return False

        # Initialize movement state BEFORE adding to entity_agents
        if isinstance(start_entity, Conveyor):
            self._agent_movement[agent] = {"progress": 0.0, "target_entity": initial_state.get("end_entity")}
        elif isinstance(start_entity, TurnTable):
            target_angle = initial_state.get("target_angle", 0.0)
            self._agent_movement[agent] = {"angle": 0.0, "target_angle": target_angle, "target_entity": initial_state.get("end_entity")}
        else:
            # Unknown entity type — fail
            return False

        # Now check collision — all other agents have guaranteed state
        if not self._can_place_agent(agent, start_entity):
            # Clean up — remove from _agent_movement since placement failed
            del self._agent_movement[agent]
            return False

        # Assign to entity — now safe to add
        self._agent_entity[agent] = start_entity
        self._entity_agents[start_entity].add(agent)

        return True

    def unregister(self, agent: BaseAgent) -> bool:
        """
        Unregister agent from space.
        Returns False if agent was not registered.
        """
        if agent not in self._agent_entity:
            return False

        entity = self._agent_entity[agent]
        self._entity_agents[entity].discard(agent)
        # if len(self._entity_agents[entity]) == 0:
        #     del self._entity_agents[entity]

        del self._agent_entity[agent]
        del self._agent_movement[agent]

        return True

    def update(self, delta_time: float) -> None:
        """
        Advance all agents by delta_time.
        Move agents, check collisions, update state.
        """
        for agent in list(self._agent_entity.keys()):
            entity = self._agent_entity[agent]
            state = self._agent_movement[agent]

            if isinstance(entity, Conveyor):
                total_length = entity.get_total_length()
                if total_length <= 0:
                    state["progress"] = 1.0
                    continue

                # Convert speed (distance/time) to progress/time
                distance_traveled = entity.speed * delta_time
                progress_increment = distance_traveled / total_length

                new_progress = state["progress"] + progress_increment
                if new_progress > 1.0:
                    new_progress = 1.0
                state["progress"] = new_progress

            elif isinstance(entity, TurnTable):
                new_angle = state["angle"] + (entity.angular_speed * delta_time)
                target_angle = state["target_angle"]
                if new_angle >= target_angle:
                    new_angle = target_angle
                state["angle"] = new_angle

    def get_state(self, agent: BaseAgent) -> Dict[str, Any]:
        """
        Get current space-specific state of agent.
        """
        if agent not in self._agent_movement:
            return {}
        return self._agent_movement[agent].copy()

    def is_movement_complete(self, agent: BaseAgent) -> bool:
        """
        Check if agent has completed movement on current entity.
        """
        if agent not in self._agent_movement:
            return False

        state = self._agent_movement[agent]
        entity = self._agent_entity[agent]

        if isinstance(entity, Conveyor):
            return state["progress"] >= 1.0
        elif isinstance(entity, TurnTable):
            return state["angle"] >= state["target_angle"]

        return False

    def _can_place_agent(self, agent: BaseAgent, entity: Any) -> bool:
        if entity not in self._entity_agents:
            return True

        if isinstance(entity, Conveyor):
            total_length = entity.get_total_length()
            if total_length == 0:
                return False
            required_progress = agent.length / total_length

            for other_agent in self._entity_agents[entity]:
                other_state = self._agent_movement[other_agent]
                other_start = other_state["progress"] - other_agent.length / total_length
                other_end = other_state["progress"]
                if other_start < required_progress and other_end > 0.0:
                    return False
                assert other_agent in self._agent_movement, f"Agent {id(other_agent)} has no movement state!"

        return True
