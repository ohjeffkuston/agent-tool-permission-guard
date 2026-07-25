"""Deterministic policy evaluation for proposed AI-agent tool calls."""

from __future__ import annotations

from copy import deepcopy
from fnmatch import fnmatchcase
from typing import Any


class PolicyError(ValueError):
    """Raised when a policy or plan cannot be evaluated safely."""


_EFFECT_RANK = {"allow": 0, "review": 1, "block": 2}


def _require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PolicyError(f"{name} must be an object")
    return value


def _require_list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise PolicyError(f"{name} must be a list")
    return value


def _unique_ids(items: list[dict[str, Any]], name: str) -> None:
    ids = [item.get("id") for item in items]
    if any(not isinstance(item_id, str) or not item_id.strip() for item_id in ids):
        raise PolicyError(f"every {name} needs a non-empty string id")
    if len(ids) != len(set(ids)):
        raise PolicyError(f"duplicate {name} id")


def _string_list(value: Any, name: str) -> list[str]:
    items = _require_list(value, name)
    if not items or any(not isinstance(item, str) or not item for item in items):
        raise PolicyError(f"{name} must contain non-empty strings")
    return items


def _validate_rule(rule: dict[str, Any]) -> None:
    effect = rule.get("effect")
    if effect not in _EFFECT_RANK:
        raise PolicyError(f"rule {rule.get('id')} has invalid effect")
    priority = rule.get("priority", 0)
    if not isinstance(priority, int):
        raise PolicyError(f"rule {rule.get('id')} priority must be an integer")
    for field in ("tools", "actions", "environments", "resources"):
        _string_list(rule.get(field, ["*"]), f"rule {rule.get('id')} {field}")
    max_risk = rule.get("max_risk", 100)
    if not isinstance(max_risk, int) or not 0 <= max_risk <= 100:
        raise PolicyError(f"rule {rule.get('id')} max_risk must be 0..100")
    if not isinstance(rule.get("require_approval", False), bool):
        raise PolicyError(f"rule {rule.get('id')} require_approval must be boolean")


def _validate_request(request: dict[str, Any]) -> None:
    for field in ("tool", "action", "environment", "resource"):
        value = request.get(field)
        if not isinstance(value, str) or not value:
            raise PolicyError(f"request {request.get('id')} needs {field}")
    risk = request.get("risk")
    if not isinstance(risk, int) or not 0 <= risk <= 100:
        raise PolicyError(f"request {request.get('id')} risk must be 0..100")


def _matches(value: str, patterns: list[str]) -> bool:
    return any(fnmatchcase(value, pattern) for pattern in patterns)


def _rule_matches(rule: dict[str, Any], request: dict[str, Any]) -> bool:
    return (
        _matches(request["tool"], rule.get("tools", ["*"]))
        and _matches(request["action"], rule.get("actions", ["*"]))
        and _matches(request["environment"], rule.get("environments", ["*"]))
        and _matches(request["resource"], rule.get("resources", ["*"]))
    )


def _evaluate_request(request: dict[str, Any], rules: list[dict[str, Any]], default: str) -> dict[str, Any]:
    matches = [rule for rule in rules if _rule_matches(rule, request)]
    if not matches:
        return {
            "request_id": request["id"],
            "decision": default.upper(),
            "matched_rule": None,
            "reason": f"no rule matched; policy default is {default}",
            "approval_required": default != "allow",
        }

    matches.sort(key=lambda rule: (-rule.get("priority", 0), -_EFFECT_RANK[rule["effect"]], rule["id"]))
    rule = matches[0]
    effect = rule["effect"]
    reason = f"matched rule {rule['id']}"
    if request["risk"] > rule.get("max_risk", 100):
        effect = "block"
        reason = f"risk {request['risk']} exceeds rule {rule['id']} limit {rule.get('max_risk', 100)}"
    elif effect == "allow" and rule.get("require_approval", False):
        effect = "review"
        reason = f"rule {rule['id']} requires human approval"

    return {
        "request_id": request["id"],
        "decision": effect.upper(),
        "matched_rule": rule["id"],
        "reason": reason,
        "approval_required": effect != "allow",
    }


def evaluate_plan(document: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a tool-call plan without executing any tool or changing state."""
    original = deepcopy(document)
    root = _require_mapping(document, "document")
    policy = _require_mapping(root.get("policy"), "policy")
    default = policy.get("default", "block")
    if default not in _EFFECT_RANK:
        raise PolicyError("policy default must be allow, review, or block")

    rules = [_require_mapping(item, "rule") for item in _require_list(policy.get("rules"), "policy rules")]
    requests = [_require_mapping(item, "request") for item in _require_list(root.get("requests"), "requests")]
    if not requests:
        raise PolicyError("requests must not be empty")
    _unique_ids(rules, "rule")
    _unique_ids(requests, "request")
    for rule in rules:
        _validate_rule(rule)
    for request in requests:
        _validate_request(request)

    findings = [_evaluate_request(request, rules, default) for request in requests]
    decision = max((item["decision"] for item in findings), key=lambda item: _EFFECT_RANK[item.lower()])
    counts = {name: sum(item["decision"] == name for item in findings) for name in ("ALLOW", "REVIEW", "BLOCK")}
    if document != original:
        raise AssertionError("evaluation mutated its input")
    return {"decision": decision, "counts": counts, "human_approval_required": decision != "ALLOW", "findings": findings}

