# RefundGuard

A hardened local TEST workspace with a production-style support UI: an AI support agent, Razorpay refunds, AgntID runtime boundaries, explicit attack replay, and a separate exact-action human approval gate.

## Run

Fill `.env` locally. Never commit it. Only `rzp_test_` keys are accepted.

From this directory, use the prepared Python environment:

```sh
../../work/agent-checkout-py312/bin/python mcp_server.py
../../work/agent-checkout-py312/bin/python app.py
```

Open http://localhost:8090. Create ticket, other-customer and baseline test payments using Checkout.

## AgntID

Add an HTTP MCP server with server ID/prefix `checkout`, URL `http://host.docker.internal:8091/mcp`. Review its tools and their classifications. Wait for runtime synchronization.

Set runtime policies:

- `get_payment`: payment ID equals the captured ticket payment.
- `refund_payment`: payment ID equals the ticket payment; `amount_paise` range 100–50000.
- `approved_refund_payment`: payment ID equals the ticket payment; `amount_paise` range 100–100000.

Use the actual discovered MCP names. AgntID enforces these limits before tool execution. The application independently checks the exact human-approved tool/payment/amount, expiry, and single-use approval. Do not claim these are a native AgntID human-approval flow.

## Demo

1. Run a valid ₹400 request in protected mode.
2. Replay a ₹1,000 normal refund: blocked by AgntID.
3. Replay a refund to another payment: blocked by AgntID.
4. Replay an approved refund without approval: application requests review.
5. Approve ₹1,000 on the ticket payment, then replay the exact approved-refund tool.
6. Change amount/payment or reuse consumed approval: no matching approval; or runtime scope denies first.
7. For the before/after comparison, use unprotected mode with the separate baseline payment and equivalent amount. This mode calls the same backend tool directly, bypassing AgntID intentionally for TEST-only demonstration.

LLM attacks are not guaranteed to produce unsafe calls. Explicit replay is labeled and never attributed to the LLM. Use AgntID Reporting for authoritative runtime decisions, and the local ledger/Razorpay test dashboard for execution proof.

## Limits

This is a local single-operator demo, not a production support system. Approvals are backed by SQLite and consumed before external execution; an uncertain network result requires manual reconciliation. No automatic refund retry. Cumulative refund limits are not implemented. Creating a new payment requires updating its fixed demo resource policies. Customer identity is simulated.

## Updated operator interface

Use the sidebar to switch between Support workspace, Execution evidence, Before & after, How it works, and Connections & setup. Evidence is loaded from real persisted receipts. Click a row for its decision explanation; use export for a credential-free JSON snapshot. Balances are read from Razorpay when explicitly requested. A pending provider refund is shown as initiated, not settled.

Approvals no longer stack: a new approval replaces previous unused approvals. Request IDs prevent duplicate submission of the same request; a new user action intentionally creates a new request. Each agent request can attempt only one refund. Unprotected comparisons are restricted server-side to the baseline payment.

For a fresh machine, use Python 3.12, install requirements.txt into a virtual environment, copy .env.example to .env, and configure the local AgntID runtime separately. Read PRODUCTION-READINESS.md before planning live deployment.

Validation: `python -m unittest test_approval.py test_workspace.py`.

## Operator-reviewed resolutions
The main support workspace now prepares a saved recommendation, using an AgntID-governed payment read and an OpenAI JSON recommendation. Preparing never refunds. The operator can reject it or execute the server-stored payment and amount once. Client-supplied amount/payment changes are ignored. Recommendations above ₹500 create a matching five-minute application approval before the approved tool call. The runtime still enforces its ₹1,000 ceiling and ticket scope.

A provider-accepted resolution blocks further resolution refunds for that payment/case. An uncertain attempt is locked as `needs_reconciliation` and requires manual provider investigation; it is never automatically retried. The controlled replay lab and legacy `/api/agent` demonstration endpoint remain separate test paths and are not production operator authorization. Customer identities are simulated. This local session token is not operator authentication.
