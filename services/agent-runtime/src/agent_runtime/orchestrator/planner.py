"""Agent execution planner: decomposes objectives into ordered tool steps."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Step:
    tool_name: str
    arguments: dict
    depends_on: list[int] = field(default_factory=list)
    description: str = ""


@dataclass
class Plan:
    objective: str
    steps: list[Step]
    estimated_tokens: int = 0


def build_plan(objective: str, available_tools: list[str], model: str = "azure/gpt-4o") -> Plan:
    """
    Use an LLM to decompose an objective into sequential tool-call steps.
    Returns a Plan with ordered Steps.
    """
    import json
    import litellm

    system_prompt = (
        "You are a planning agent. Given an objective and a list of available tools, "
        "produce a JSON execution plan.\n"
        "Return ONLY a JSON object with keys: 'steps' (array), each step has: "
        "'tool_name' (string), 'arguments' (object), 'depends_on' (array of step indices), "
        "'description' (string)."
    )
    user_prompt = f"Objective: {objective}\nAvailable tools: {', '.join(available_tools)}"

    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1024,
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        raw = json.loads(response.choices[0].message.content)
        steps = [
            Step(
                tool_name=s["tool_name"],
                arguments=s.get("arguments", {}),
                depends_on=s.get("depends_on", []),
                description=s.get("description", ""),
            )
            for s in raw.get("steps", [])
        ]
        tokens = response.usage.total_tokens if response.usage else 0
        return Plan(objective=objective, steps=steps, estimated_tokens=tokens)
    except Exception:
        return Plan(objective=objective, steps=[], estimated_tokens=0)
