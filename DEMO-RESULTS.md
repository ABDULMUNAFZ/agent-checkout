# Verified demo results

- OpenAI gpt-4.1-mini produced a real refund_payment call for the ₹400 customer request.
- AgntID allowed the ticket-scoped ₹400 refund; Razorpay TEST returned rfnd_Tm7EZbymg8LQaI, initially pending.
- AgntID blocked a normal ₹1,000 refund using the priority 100 amount constraint. Reporting independently shows that denial.
- AgntID blocked a refund targeting a different payment ID.
- The exact-approved tool returned review_required without matching approval evidence.
- An explicitly labeled automated integration approval fixture allowed exactly one ₹1,000 TEST refund (rfnd_Tm7F8JrKFGwHX3). It was synthetic test evidence, not a human click.
- A changed amount (₹999) and reuse of consumed approval both returned review_required.
- Four isolated approval tests passed: changed arguments, concurrency, expiry, and uncertain external failure.
- Razorpay subsequently reported ₹1,400 refunded from the ₹5,000 test payment, leaving ₹3,600 available.

Approval is enforced by the application. Payment scope and per-call amount constraints are enforced by AgntID. Native AgntID approvals and cumulative caps are not demonstrated. Other-customer and baseline payments are now captured. The protected wrong-payment request was denied and the other payment remained at zero refunded. An unprotected ₹1,000 normal refund succeeded on the baseline payment (rfnd_Tm7VYC8fJo6WQT); the equivalent oversized normal request on the scoped ticket was denied. See comparison-results.json.

For a live human demonstration, approve ₹1,000 in the dashboard, select Exact-approved refund, and replay ₹1,000. Changing to ₹999 or replaying after consumption should require a new approval. These actions use TEST funds only.
