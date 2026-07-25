# Agent Tool Permission Guard: Authorization Before an AI Agent Can Act

An AI agent that can call tools is not merely a chatbot. It may be able to query production systems, modify cloud resources, create access grants, or initiate deployments. That capability needs an authorization boundary stronger than natural-language instructions.

![Agent Tool Permission Guard architecture](https://raw.githubusercontent.com/ohjeffkuston/agent-tool-permission-guard/main/docs/architecture.png)

## The enterprise risk behind tool-enabled agents

Imagine an operations agent diagnosing an incident. It reads metrics, identifies a likely failed instance, and proposes a termination call. The reasoning may sound correct while the target, environment, or risk context is wrong.

Prompt injection is one concern, but it is not the only one. Over-broad permissions, stale context, ambiguous resources, incorrect environment labels, and unreviewed production actions can all create a dangerous path from model output to infrastructure change.

## A deterministic authorization boundary

I built **Agent Tool Permission Guard** as a model-independent policy layer for proposed tool calls. It evaluates a recorded plan containing the tool, action, environment, resource, and risk score. Version-controlled rules then produce an explainable `ALLOW`, `REVIEW`, or `BLOCK` decision.

The evaluator uses explicit priority, glob matching, risk limits, restrictive tie-breaking, and a fail-closed default. A rule can also require approval, converting an otherwise allowed request into human review.

## Five controls that make the boundary useful

- **Context-aware rules:** tool, action, environment, and resource are evaluated together.
- **Risk ceilings:** a request exceeding a rule's threshold is blocked.
- **Human approval:** sensitive operations stop even when a rule otherwise allows them.
- **Deterministic conflicts:** priority wins first; restrictive effects win ties.
- **Fail-closed validation:** unknown or malformed plans do not drift into execution.

## Integrating with n8n and CI/CD

The repository includes an inactive n8n workflow that accepts a proposed tool-call plan, runs the local evaluator, and routes only `ALLOW` to an authorized response. `REVIEW` and `BLOCK` both stop for human judgment.

GitHub Actions runs ten unit tests and validates every JSON artifact. Policies and synthetic plans can therefore be reviewed like code before they protect a real workflow.

## The safety boundary is deliberate

The project calls no model, stores no credentials, executes no tool, and changes no infrastructure. It belongs before a separate executor. In production, environment and risk context should come from trusted server-side systems rather than untrusted model output.

This separation is the core design principle: the model proposes, deterministic policy constrains, and humans retain authority over consequential actions.

Source code, tests, architecture, Docker guidance, and the n8n example are available on GitHub:

https://github.com/ohjeffkuston/agent-tool-permission-guard

