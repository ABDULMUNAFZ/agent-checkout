# RefundGuard: production readiness

## What this release provides

A production-style, responsive support workspace for a simulated e-commerce case, backed by real OpenAI calls, a local AgntID runtime and Razorpay TEST. Existing financial evidence is preserved. Production infrastructure is not provisioned and live-mode payment keys remain rejected.

- Support workspace with a ticket, permitted payment, realistic messages, observable outcome and balance lookup.
- Execution evidence with search, outcome filters, selected-call explanation, request IDs, raw JSON on demand and credential-free export.
- Before/after comparison populated from actual historical receipts, with separate baseline and customer payments.
- Workflow explanation that distinguishes AgntID parameter enforcement from the application's approval gate.
- One active application approval at a time, exact arguments, expiry, single use and explicit revocation.
- Durable request reservation and result replay for a repeated request ID. Reusing an ID with changed payload is rejected.
- One refund attempt per agent request, no automatic retry of uncertain refund outcomes, input/path validation, session token, same-origin checks and host validation.
- SQLite WAL and durable request/evidence persistence. This is not a tamper-evident external audit store.

## Real-world business flow

A customer reports a damaged product. The support agent receives a case identity and associated payment from trusted case data, not from customer text. A normal refund must satisfy the ticket resource and per-call amount policy. A larger permitted refund needs a supervisor's exact approval. The payment connector executes only after these checks and provider events reconcile the final refund status. Security and finance teams inspect the decision and settlement evidence separately.

This release simulates the customer/case binding and local operator. AgntID enforces the fixed payment and amount policies reviewed in the console. Native intent-based enforcement, derived ephemeral payment credentials and native AgntID human approvals are not validated here.

## Required before live deployment

1. **Identity:** authenticate operators using organization SSO; derive actor and tenant from a verified session. Introduce separate support and supervisor roles, approval authorization and case ownership checks. Never accept these identities from arbitrary client payloads.
2. **Isolation:** replace shared demo slots with tenant-scoped cases and payment mappings. Put the payment MCP on a private authenticated network. The current loopback service has no MCP authentication and must not be exposed publicly.
3. **Secrets:** move provider keys to a secrets manager with rotation and narrowly controlled connector access. Keep live keys out of the model's tool arguments and output.
4. **Money correctness:** reserve a cumulative per-case refund budget, verify refundable balance atomically with business rules, use documented provider idempotency where supported, and reconcile signed provider webhooks. A network timeout is an unknown outcome, not proof of failure.
5. **Durability:** migrate SQLite and in-process locks to a transactional database and durable job queue. Reconcile abandoned running requests after crashes. Retain immutable audit records outside the application.
6. **Governance:** configure task/resource bindings dynamically and independently validate AgntID intent and credential features before claiming them. Fixed demo scope must be refreshed when changing the ticket fixture.
7. **Operations:** deploy behind TLS, authenticated access, rate limits and observability; complete privacy, dependency and security review. Remove unprotected replay routes entirely from a live deployment.

These remaining requirements are material. A polished local TEST app is not yet a production payment system.

## Source alignment

Reviewed all nine rendered slides in AgntID-Hackathon-Deck.pdf. The one-resource example, independent per-tool-call evaluation, customer-hosted execution plane and operator audit workflow inform the new case, comparison and evidence views.

Official website reviewed: https://agntid.ai/

## Validation

14 approval and API tests pass and run without real provider writes. Browser checks cover actual runtime denial, live payment balances, read-only LLM tool calling, navigation, filtering, inspector selection, guide dialog and evidence export. Historic provider refund receipts populate the comparison; no new baseline refund is needed to view it.

### Resolution workflow added
Saved proposal → operator review/reject → exact server-stored execution → persisted initiated/blocked/reconciliation state. Duplicate execution and changed ticket mappings are rejected. Available provider balance is rechecked before a refund. Provider acceptance is not final settlement; webhook reconciliation and authenticated operator identity remain required for deployment. The legacy direct agent endpoint and replay lab must be removed or restricted to an isolated test environment before production.
