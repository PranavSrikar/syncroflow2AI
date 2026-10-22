"""Executable real-SUMO emergency demonstration through the existing API.

Run with backend/.venv/Scripts/python.exe scripts/demo_emergency.py.
Requires the backend; refuses to reset an already connected simulation.
"""
import argparse
import json
import httpx


def run(base_url):
    with httpx.Client(base_url=base_url.rstrip("/") + "/api/v1/sumo/", timeout=30) as client:
        state = client.get("status").json()
        if state["connected"]:
            raise RuntimeError("Stop the existing simulation before running this demonstration")
        def post(path, **kwargs):
            response = client.post(path, **kwargs)
            response.raise_for_status()
            return response.json()
        try:
            post("start", params={"scenario": "pedestrian", "controller": "mpc"})
            post("pause")
            ids = [post("emergencies/inject", json={"approach": a, "priority": p})["vehicleId"] for a, p in (("east", 3), ("north", 1))]
            for _ in range(280):
                post("step")
                status = client.get("emergencies/status").json()
                rows = {r["vehicleId"]: r for r in status["requests"]}
                if all(rows[v]["state"] == "completed" for v in ids):
                    print(json.dumps(status, indent=2))
                    return
            raise RuntimeError("Emergency requests did not complete within the simulation budget")
        finally:
            post("stop")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8001")
    run(parser.parse_args().url)
