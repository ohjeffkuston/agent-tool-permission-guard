Hello Jeffrey,

Day 9 of your Cloud + AI portfolio is Agent Tool Permission Guard.

PROJECT PURPOSE

Tool-enabled AI agents can move beyond generating text and request actions against cloud platforms, ticketing systems, deployment tools, and operational data. This project places a deterministic policy-as-code boundary between an agent's proposed plan and any real executor. It returns ALLOW, REVIEW, or BLOCK without calling a model or running a tool.

ARCHITECTURE

1. Tool-call plan: the proposed tool, action, environment, resource, and risk enter as data.
2. Policy engine: priority, glob matching, risk limits, approval flags, and restrictive tie-breaking are evaluated deterministically.
3. Decision report: each request receives a matched rule, reason, approval flag, and final effect.
4. Safety boundary: only ALLOW can proceed to a separate executor; REVIEW and BLOCK stop for human judgment.

HOW THE CODE WORKS

- `engine.py` validates every policy and request, rejects duplicate IDs, matches explicit patterns, selects rules by priority, blocks excessive risk, upgrades approval-gated ALLOW to REVIEW, and produces stable JSON.
- `cli.py` reads a JSON plan and exits 0 only for an all-ALLOW result. REVIEW or BLOCK exits 1; malformed input exits 2 with a fail-closed report.
- `tests/test_engine.py` covers safe reads, unknown actions, approval gates, risk thresholds, priority, restrictive ties, mixed plans, duplicate IDs, invalid risk, deterministic output, and input immutability.
- `examples/tool-call-plan.json` includes a safe development query, a production read that needs review, and a destructive production action that is blocked.
- `n8n/permission-gate-workflow.json` is an inactive approval-first integration example.
- `.github/workflows/ci.yml` runs unit tests, compiles Python, and validates JSON.

HOW TO RUN IT

From the project directory:

`PYTHONPATH=src python -m unittest discover -s tests -v`

Then evaluate the sample:

`PYTHONPATH=src python -m agent_tool_permission_guard examples/tool-call-plan.json`

The sample intentionally returns BLOCK and exits 1. Read the findings; that non-zero exit is the policy gate working correctly.

HOW TO CHANGE THE POLICY

Each rule has an ID, priority, effect, matching patterns, optional maximum risk, and optional approval requirement. Higher priority wins. If priorities tie, BLOCK wins over REVIEW, and REVIEW wins over ALLOW. If nothing matches, the default should remain BLOCK.

SAFE DEPLOYMENT PRACTICE

- Keep the gate separate from the tool executor.
- Derive environment, identity, and risk from trusted server-side context.
- Never let the model choose its own permissions.
- Protect policy changes with branch review and passing CI.
- Use least-privilege credentials only in the downstream executor.
- Log policy decisions without storing secrets or sensitive payloads.
- Require human approval for production, destructive, identity, and credential actions.

WHAT TO LEARN

Be ready to explain the difference between agent planning and authorization. Prompt instructions influence behavior; deterministic policy controls permission. Understand priority, restrictive tie-breaking, risk ceilings, fail-closed defaults, and why the authorization layer must run before every consequential tool call.

INTERVIEW POSITIONING

Use this project when asked about safe AI orchestration:

“I built a deterministic authorization guard for AI-agent tool-call plans. It evaluates tool, action, environment, resource, and risk against version-controlled policy, then returns ALLOW, REVIEW, or BLOCK with case-level reasons. It never calls a model or executes a tool, so it can sit as a clear security boundary before n8n or another executor.”

Likely follow-up questions:

- Why not rely on the system prompt? Prompts guide model behavior but are not an enforceable authorization boundary.
- Why evaluate each tool call? A safe plan can become unsafe when context, target, or arguments change between steps.
- How would you extend it? Add authenticated actor identity, signed policy bundles, time-bound grants, argument schemas, audit storage, and Open Policy Agent integration.
- What is the main failure mode? Unknown and malformed inputs fail closed, and every non-ALLOW outcome requires human review.

Portfolio links:

GitHub: https://github.com/ohjeffkuston/agent-tool-permission-guard
Architecture: https://raw.githubusercontent.com/ohjeffkuston/agent-tool-permission-guard/main/docs/architecture.png

Regards,
Your Cloud + AI Portfolio Automation

