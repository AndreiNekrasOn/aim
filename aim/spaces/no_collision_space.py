from typing import Dict, Any, List, Optional, Set, Tuple
from aim.core.space import SpaceManager
from aim.core.agent import BaseAgent

Point3D = Tuple[float, float, float]

class NoCollisionSpace(SpaceManager):
    """
    Manages agents moving in 3D space without collisions.
    Agents move at constant speed toward target position.
    """

    def __init__(self):
        # Agent -> current position
        self._agent_position: Dict[BaseAgent, Point3D] = {}
        # Agent -> target position
        self._agent_target: Dict[BaseAgent, Point3D] = {}
        # Agent -> speed
        self._agent_speed: Dict[BaseAgent, float] = {}

    def register(self, agent: BaseAgent, initial_state: Dict[str, Any]) -> bool:
        """
        Register agent with initial state.
        Expected keys: "start_position", "target_position", "speed".
        """
        start_position = initial_state.get("start_position")
        target_position = initial_state.get("target_position")
        speed = initial_state.get("speed", 1.0)

        if start_position is None or target_position is None:
            print(start_position)
            print(target_position)
            print('here,0')
            return False

        if not isinstance(start_position, tuple) or len(start_position) != 3:
            print('here,1')
            return False
        if not isinstance(target_position, tuple) or len(target_position) != 3:
            print('here,2')
            return False
        if speed <= 0:
            print('here,3')
            return False

        # Initialize space_state
        agent.space_state = {
            "position": start_position,
            "target": target_position,
            "speed": speed,
            "progress": 0.0
        }

        # Track internally
        self._agent_position[agent] = start_position
        self._agent_target[agent] = target_position
        self._agent_speed[agent] = speed

        return True

    def unregister(self, agent: BaseAgent) -> bool:
        """
        Unregister agent from space.
        """
        if agent not in self._agent_position:
            return False

        del self._agent_position[agent]
        del self._agent_target[agent]
        del self._agent_speed[agent]

        agent.space_state = {}
        return True

    def update(self, delta_time: float) -> None:
        """
        Advance all agents by delta_time.
        Move agents toward target at constant speed.
        """
        for agent in list(self._agent_position.keys()):
            state = agent.space_state
            if not state:
                continue

            current_pos = self._agent_position[agent]
            target_pos = self._agent_target[agent]
            speed = self._agent_speed[agent]

            # Compute direction vector
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
