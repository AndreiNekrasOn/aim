# examples/boltzmann_wealth_transfer.py

from aim import BaseAgent, Simulator
from typing import List
import random

class WealthAgent(BaseAgent):
    next_id = 0

    def __init__(self, initial_wealth: float = 100.0):
        super().__init__()
        self.wealth = initial_wealth
        self.agent_id = WealthAgent.next_id
        WealthAgent.next_id += 1


def run_market(sim: Simulator, agents: List[WealthAgent], tick: int):
    """
    Scheduled market event: pairs agents randomly.
    Each pair: one agent sends a random amount (up to its wealth) to the other.
    """
    if len(agents) < 2:
        return

    shuffled = agents[:]
    random.shuffle(shuffled)

    for i in range(0, len(shuffled) - 1, 2):
        a = shuffled[i]
        b = shuffled[i + 1]

        # Agent A sends random amount to B — capped by A's wealth
        send_amount = random.uniform(0, a.wealth)
        a.wealth -= send_amount
        b.wealth += send_amount


# --- SIMULATION SETUP ---

sim = Simulator(max_ticks=100, random_seed=42)
agents = [WealthAgent() for _ in range(100)]

for agent in agents:
    sim.add_agent(agent)

sim.schedule_event(
    lambda tick: run_market(sim, agents, tick),
    delay_ticks=1,
    recurring=True
)

sim.run()

# --- RESULTS ---
agents_sorted = sorted([agent.wealth for agent in agents], reverse=True)
print("\nTop 10 wealthiest agents:")
for i in range(min(10, len(agents_sorted))):
    print(f"  Agent {i+1}: ${agents_sorted[i]:.2f}")

total_final = sum(agents_sorted)
print(f"\nFinal total wealth: ${total_final:.2f} (started with $10000)")
