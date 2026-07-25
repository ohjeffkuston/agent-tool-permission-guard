import copy
import unittest

from agent_tool_permission_guard import PolicyError, evaluate_plan


def document(requests, rules=None, default="block"):
    return {
        "policy": {
            "default": default,
            "rules": rules or [{"id": "read-dev", "priority": 10, "effect": "allow", "tools": ["cloud-api"], "actions": ["read", "list"], "environments": ["dev", "staging"], "resources": ["aws:*"], "max_risk": 30}],
        },
        "requests": requests,
    }


class EvaluatePlanTests(unittest.TestCase):
    def test_safe_read_is_allowed(self):
        result = evaluate_plan(document([{"id": "r1", "tool": "cloud-api", "action": "read", "environment": "dev", "resource": "aws:s3:demo", "risk": 10}]))
        self.assertEqual(result["decision"], "ALLOW")

    def test_unknown_action_fails_closed(self):
        result = evaluate_plan(document([{"id": "r1", "tool": "cloud-api", "action": "delete", "environment": "dev", "resource": "aws:s3:demo", "risk": 10}]))
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIsNone(result["findings"][0]["matched_rule"])

    def test_approval_upgrades_allow_to_review(self):
        rules = [{"id": "prod-read", "priority": 20, "effect": "allow", "tools": ["cloud-api"], "actions": ["read"], "environments": ["prod"], "resources": ["*"], "max_risk": 50, "require_approval": True}]
        result = evaluate_plan(document([{"id": "r1", "tool": "cloud-api", "action": "read", "environment": "prod", "resource": "aws:ec2:i-1", "risk": 20}], rules))
        self.assertEqual(result["decision"], "REVIEW")

    def test_risk_limit_blocks(self):
        result = evaluate_plan(document([{"id": "r1", "tool": "cloud-api", "action": "read", "environment": "dev", "resource": "aws:s3:demo", "risk": 80}]))
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("exceeds", result["findings"][0]["reason"])

    def test_highest_priority_rule_wins(self):
        rules = [
            {"id": "broad-block", "priority": 1, "effect": "block", "tools": ["*"], "actions": ["*"], "environments": ["*"], "resources": ["*"]},
            {"id": "specific-allow", "priority": 10, "effect": "allow", "tools": ["ticketing"], "actions": ["create"], "environments": ["prod"], "resources": ["incident:*"], "max_risk": 20},
        ]
        result = evaluate_plan(document([{"id": "r1", "tool": "ticketing", "action": "create", "environment": "prod", "resource": "incident:123", "risk": 10}], rules))
        self.assertEqual(result["decision"], "ALLOW")

    def test_restrictive_tie_wins(self):
        rules = [
            {"id": "allow", "priority": 5, "effect": "allow", "tools": ["*"], "actions": ["*"], "environments": ["*"], "resources": ["*"]},
            {"id": "block", "priority": 5, "effect": "block", "tools": ["*"], "actions": ["*"], "environments": ["*"], "resources": ["*"]},
        ]
        result = evaluate_plan(document([{"id": "r1", "tool": "x", "action": "y", "environment": "dev", "resource": "z", "risk": 1}], rules))
        self.assertEqual(result["decision"], "BLOCK")

    def test_plan_decision_uses_most_restrictive_request(self):
        requests = [
            {"id": "r1", "tool": "cloud-api", "action": "read", "environment": "dev", "resource": "aws:s3:demo", "risk": 10},
            {"id": "r2", "tool": "cloud-api", "action": "delete", "environment": "prod", "resource": "aws:s3:demo", "risk": 90},
        ]
        result = evaluate_plan(document(requests))
        self.assertEqual(result["counts"], {"ALLOW": 1, "REVIEW": 0, "BLOCK": 1})
        self.assertTrue(result["human_approval_required"])

    def test_duplicate_request_ids_fail_closed(self):
        requests = [
            {"id": "same", "tool": "x", "action": "y", "environment": "dev", "resource": "z", "risk": 1},
            {"id": "same", "tool": "x", "action": "y", "environment": "dev", "resource": "z", "risk": 1},
        ]
        with self.assertRaises(PolicyError):
            evaluate_plan(document(requests))

    def test_invalid_risk_fails_closed(self):
        with self.assertRaises(PolicyError):
            evaluate_plan(document([{"id": "r1", "tool": "x", "action": "y", "environment": "dev", "resource": "z", "risk": 101}]))

    def test_deterministic_and_input_unchanged(self):
        payload = document([{"id": "r1", "tool": "cloud-api", "action": "read", "environment": "dev", "resource": "aws:s3:demo", "risk": 10}])
        original = copy.deepcopy(payload)
        self.assertEqual(evaluate_plan(payload), evaluate_plan(payload))
        self.assertEqual(payload, original)


if __name__ == "__main__":
    unittest.main()

