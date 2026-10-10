# AWS deployment

Live operator workspace: https://abdul.runs-on.dev

RefundGuard runs on an Amazon Linux EC2 instance in Mumbai with Docker Compose. Caddy provides HTTPS and operator authentication. Only ports 80 and 443 are public. The AgntID runtime UI and MCP proxy bind to loopback; the Razorpay TEST MCP service stays inside Docker. Administration uses AWS Systems Manager.

## Deploy from source

1. Provision a suitable x86 VM with Docker, Compose and Buildx. Allow inbound HTTP/HTTPS and use private administrative access.
2. Clone this repository. Copy `deploy/.env.example` to `deploy/.env`, restrict its permissions to 600, and populate TEST provider keys, the LLM key, public origin, and operator password hash. Keep secrets out of Git.
3. Run `docker compose -p refundguard --env-file deploy/.env -f deploy/compose.yml up -d --build`.
4. Bootstrap AgntID through a private tunnel to port 8080. Register checkout at `http://payment-mcp:8091/mcp`, review the three tools, and configure exact ticket-payment policies: normal refunds 100–50000 paise; approved refunds up to 100000 paise. The approval tool also enforces a bound, expiring application approval.
5. Create and capture a Razorpay TEST ticket payment, then update the exact payment IDs in AgntID. Set the domain A record to the VM IPv4. Caddy obtains its certificate automatically.
6. Verify governed reads, saved recommendations, operator execution, provider receipts, duplicate rejection, policy denials, and data persistence after restart.

## Existing runtime migration

Stop the old runtime before transferring its identity and persistent config/data through a private channel. Do not run two copies of the same identity. Preserve database consistency and volume ownership: the deployed AgntID image uses UID/GID 1001; RefundGuard uses UID/GID 10001. Inspect image user IDs when changing versions. The private `host.docker.internal` alias preserves the existing checkout MCP URL during this deployment. Never commit runtime identity files or databases.

## Verified on October 10, 2026

HTTPS and authenticated assets/API return successfully. AgntID governed payment lookup works. The saved 40000-paise proposal produced a Razorpay TEST refund receipt. Identical request retries return the same result; a new attempt on that proposal is rejected. A 100000-paise normal refund and another payment lookup are denied by AgntID. Hosted advanced replay returns 403. Persistent state survives app restart.

This is a single-operator TEST deployment. Provider acceptance can initially be pending; uncertain outcomes require manual reconciliation. Customer identity in the example is simulated. Multi-tenant authentication, webhook reconciliation and production payment operations are not implemented.

The credit-funded EC2 deployment has a seven-day shutdown timer for October 17, 2026 at 15:27 IST. The current instance costs approximately $0.08479/hour for compute, with storage and public IPv4 additional. Stopped instances retain billable EBS storage. A monthly $45 budget tracker is configured; email alerts are not configured. Renewing hosting requires reviewing remaining credits and the shutdown timer. Auto-assigned public IPv4 can change after stop/start, requiring a DNS update.
