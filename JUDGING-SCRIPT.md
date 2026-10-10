# RefundGuard: judging script

## Pitch
AI support agents can resolve refund requests, but customer text should never grant financial authority. RefundGuard gives the model payment tools behind AgntID: only the ticket payment and a limited amount are allowed. Larger refunds require a separate exact-action application approval that expires and can be used once.

## Three-minute demo
1. Show the ticket and explain the ₹500 normal refund limit.
2. Show the real LLM ₹400 refund receipt. The model proposed the action, AgntID permitted it, and Razorpay TEST returned a refund ID.
3. Show the unprotected ₹1,000 normal refund on the separate baseline payment. Explain that this is a deterministic attack replay, not an LLM-generated call.
4. In protected mode, replay a ₹1,000 normal refund on the ticket. Show the amount denial and AgntID Reporting.
5. Select the other-customer payment and replay ₹400 in protected mode. Show payment-scope denial; the other payment remains untouched.
6. Select Exact-approved refund. Show review_required without approval. Approve a small exact amount that fits the remaining test balance, replay it once, then replay again without approving. Show single-use rejection. To show mismatch, approve one amount and replay a different amount.
7. Close: authority comes from runtime policy and precise approval evidence, rather than words in a customer message.

## Honest claims
AgntID enforces tool visibility, payment ID and per-call amount constraints. The application enforces exact approval, expiry and single use. The approval gate is not a validated native AgntID approval flow. Customer identity is simulated; cumulative refund limits are not implemented. All payment activity is Razorpay TEST. The LLM can refuse an attack itself; replay proves the runtime boundary independently.

## Submission copy
RefundGuard is a test-mode support agent that demonstrates enforceable financial boundaries with AgntID. It combines an OpenAI tool-calling support flow, Razorpay TEST payments/refunds, ticket-scoped AgntID policies, explicit protected/unprotected attack replay, and an application approval gate bound to one tool, payment and amount. Real decision receipts and downstream payment evidence show what executed and what was blocked.

## Redesigned workspace navigation
Use Before & after for the comparison; Execution evidence for filtered receipts and the call inspector; Support workspace for the actual agent and Runtime replay lab; How it works for verified capabilities and production boundaries. The Demo guide button opens an in-app walkthrough.
