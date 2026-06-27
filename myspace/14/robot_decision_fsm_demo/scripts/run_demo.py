from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.simulator import DecisionSimulator, load_config, run_headless, run_interactive


def load_agent(agent_name: str, config):
    module = importlib.import_module(f"agents.{agent_name}")
    if not hasattr(module, "DecisionAgent"):
        raise RuntimeError(f"agents/{agent_name}.py must define DecisionAgent")
    agent = module.DecisionAgent()
    agent.reset(config)
    return agent


def parse_args():
    parser = argparse.ArgumentParser(description="RoboCup-style robot decision FSM demo")
    parser.add_argument("--agent", default="baseline_fsm", help="agent file name under agents/, without .py")
    parser.add_argument("--config", default=str(ROOT_DIR / "config" / "demo_config.json"))
    parser.add_argument("--headless", action="store_true", help="run without opening a pygame window")
    parser.add_argument("--steps", type=int, default=1200, help="simulation steps for headless mode")
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config(Path(args.config))
    agent = load_agent(args.agent, config)
    sim = DecisionSimulator(config=config, agent=agent, root_dir=ROOT_DIR)

    if args.headless:
        run_headless(sim, args.steps)
    else:
        try:
            run_interactive(sim)
        except RuntimeError as exc:
            print(str(exc))
            raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
