"""CTDE training uses the same HybridNetwork controller path as the API."""
from pathlib import Path
import numpy as np
import traci
from app.services.sumo_network_safety import NetworkSafetyModel
from app.services.hybrid_network import HybridNetwork, direction


class MultiJunctionEnv:
    agents = ("A0", "B0")
    observation_size = 8
    action_size = 2
    direction = staticmethod(direction)

    def __init__(self, episode_seconds=180, decision_seconds=5, mode="mpc"):
        if mode not in {"mpc", "max_pressure", "fixed_time"}:
            raise ValueError("Unknown research baseline")
        if episode_seconds <= 0 or decision_seconds <= 0:
            raise ValueError("Positive episode and decision duration required")
        self.episode_seconds, self.decision_seconds, self.mode = episode_seconds, decision_seconds, mode
        self.folder = Path(__file__).resolve().parents[2] / "sumo_scenarios/two_junction"
        self.connected = False

    def reset(self, seed=42):
        self.close()
        if traci.isLoaded():
            raise RuntimeError("Training must not take over an existing TraCI simulation")
        self.model = NetworkSafetyModel(self.folder / "corridor.net.xml")
        traci.start(["sumo", "-c", str(self.folder / "corridor.sumocfg"), "--seed", str(seed), "--no-step-log"], label="mappo_research")
        self.connected = True
        try:
            self.network = HybridNetwork(self.model, 'sumo_fixed_time' if self.mode == 'fixed_time' else self.mode)
            self.readers, self.estimators, self.controllers = self.network.readers, self.network.estimators, self.network.controllers
            self.raw = self.network.raw
            return self.observations()
        except Exception:
            self.close()
            raise

    def read(self):
        self.network.raw = self.network.read()
        self.raw = self.network.raw
        return self.raw

    def observations(self):
        return self.network.observations()

    def step(self, recommendations):
        if not self.connected:
            raise RuntimeError("Reset the research environment first")
        actions = None if recommendations is None else self.network.coordinator.validate_actions(recommendations)
        rewards = np.zeros(len(self.agents), dtype=np.float32)
        total_arrived = 0
        for _ in range(self.decision_seconds):
            self.network.before_step(training_actions=actions)
            traci.simulationStep()
            reward, arrived = self.network.after_step()
            rewards += reward
            total_arrived += arrived
            self.raw = self.network.raw
            if traci.simulation.getTime() >= self.episode_seconds:
                break
        truncated = traci.simulation.getTime() >= self.episode_seconds
        info = {"source": "sumo_traci", "simTime": traci.simulation.getTime(), "arrivedVehicles": total_arrived,
                "controller": self.mode, "supervisors": {a: c.supervisor.report() for a, c in self.controllers.items()},
                "coordinationRecommendations": actions.tolist() if actions is not None else None,
                "metrics": self.network.snapshot()['metrics']}
        return self.observations(), rewards, False, truncated, info

    def close(self):
        if self.connected:
            try:
                traci.switch("mappo_research")
                traci.close()
            finally:
                self.connected = False
