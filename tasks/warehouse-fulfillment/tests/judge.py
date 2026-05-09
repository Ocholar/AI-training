#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path


def write_reward(path: Path, reward: float, justification: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"reward": round(float(reward), 4)}, indent=2), encoding="utf-8")
    Path("/logs/agent").mkdir(parents=True, exist_ok=True)
    Path("/logs/agent/judge_justification.txt").write_text(justification, encoding="utf-8")


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def exact_match(agent, oracle) -> bool:
    return agent == oracle


def basic_structural_checks(agent):
    required = ["order_fulfillment_plan", "warehouse_picking_lists", "fulfillment_conflict_report"]
    if not isinstance(agent, dict):
        return False, "Top-level output must be a JSON object."
    missing = [k for k in required if k not in agent]
    if missing:
        return False, f"Missing required top-level keys: {missing}"
    if not isinstance(agent["order_fulfillment_plan"], list) or len(agent["order_fulfillment_plan"]) < 80:
        return False, "order_fulfillment_plan must be a list covering all orders."
    if not isinstance(agent["warehouse_picking_lists"], list) or len(agent["warehouse_picking_lists"]) < 8:
        return False, "warehouse_picking_lists must cover warehouse zones."
    if not isinstance(agent["fulfillment_conflict_report"], dict):
        return False, "fulfillment_conflict_report must be an object."
    return True, "Structural checks passed."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-output", required=True)
    parser.add_argument("--oracle", required=True)
    parser.add_argument("--reward-out", required=True)
    args = parser.parse_args()

    reward_out = Path(args.reward_out)
    try:
        agent = load_json(Path(args.agent_output))
    except FileNotFoundError:
        write_reward(reward_out, 0.0, "Agent did not write /logs/agent/output.json.")
        return 0
    except Exception as e:
        write_reward(reward_out, 0.0, f"Could not parse agent output JSON: {e}")
        return 0

    try:
        oracle = load_json(Path(args.oracle))
    except Exception as e:
        write_reward(reward_out, 0.0, f"Could not load oracle JSON: {e}")
        return 0

    if exact_match(agent, oracle):
        write_reward(reward_out, 1.0, "Exact match with oracle.json. Oracle shortcut passed.")
        return 0

    ok, msg = basic_structural_checks(agent)
    if not ok:
        write_reward(reward_out, 0.0, msg)
        return 0

    api_key = os.getenv("FIREWORKS_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        write_reward(reward_out, 0.0, "No FIREWORKS_API_KEY or OPENAI_API_KEY available for LLM judge.")
        return 0

    try:
        from openai import OpenAI
        base_url = os.getenv("OPENAI_BASE_URL") or "https://api.fireworks.ai/inference/v1"
        model = os.getenv("JUDGE_MODEL") or "accounts/fireworks/models/kimi-k2p5"
        client = OpenAI(api_key=api_key, base_url=base_url)
        prompt = f"""
You are grading a warehouse fulfillment planning task. Compare the AGENT_OUTPUT against the ORACLE.

Score from 0.0 to 1.0 using these weights:
- 0.20: covers every input order exactly once with valid order IDs and plausible status values.
- 0.20: item allocations are plausible and do not oversell inventory relative to the oracle's allocation strategy.
- 0.15: priority and SLA handling are reasonable, especially for CRITICAL/HIGH orders and earlier deadlines.
- 0.15: warehouse picking lists correctly aggregate allocated quantities by zone and SKU.
- 0.15: conflict report identifies real shortfalls, partial fulfillments, SLA risks, and resolutions.
- 0.10: cold-chain/handling restrictions and zone constraints are respected.
- 0.05: explanation quality is clear and audit-ready.

Accept semantically equivalent allocation plans if they obey inventory, priority, SLA, and zone constraints. Penalize dummy, empty, placeholder, or count-only outputs heavily even if the JSON shape is correct.

Return ONLY JSON in this format:
{{"reward": <float between 0 and 1>, "justification": "<brief field-by-field rationale>"}}

ORACLE:
{json.dumps(oracle)[:250000]}

AGENT_OUTPUT:
{json.dumps(agent)[:250000]}
"""
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw = resp.choices[0].message.content or ""
        m = re.search(r"\{.*\}", raw, flags=re.S)
        if not m:
            raise ValueError(f"Judge returned non-JSON response: {raw[:500]}")
        judged = json.loads(m.group(0))
        reward = max(0.0, min(1.0, float(judged.get("reward", 0.0))))
        justification = str(judged.get("justification", "No justification returned."))
        write_reward(reward_out, reward, justification)
        return 0
    except Exception as e:
        write_reward(reward_out, 0.0, f"LLM judge failed: {e}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
