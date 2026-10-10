# Free cloud deployment: not deployed yet
Target: https://abdul.runs-on.dev, Oracle Always Free only.

1. Finish Oracle signup and ensure an Always Free eligible VM is available. Verify both AgntID images support its architecture before creating it. Do not upgrade to paid resources.
2. Install Docker from its official repository. Only publish ports 80/443; restrict SSH to the operator. Runtime UI remains loopback-only.
3. Upload this source (never publicly upload .env or runtime data). Copy deploy/.env.example to deploy/.env, mode 600, and fill credentials plus the Caddy password hash. Never commit secrets.
4. Build and launch: docker compose --env-file deploy/.env -f deploy/compose.yml up -d --build
5. Via an SSH tunnel to port 8080, bootstrap a NEW AgntID runtime in the console. Configure checkout MCP as http://payment-mcp:8091/mcp. Copy reviewed tools and ticket-scoped amount policies to that runtime; do not assume the old runtime policy applies to a new runtime.
6. Create a TEST ticket payment via the authenticated app. Update exact payment policies in AgntID before proposing or resolving. Optionally migrate the existing database through a secure channel; never expose it publicly.
7. In runs-on.dev update abdul's A record to the actual public VM IPv4, preserve owner and claimedAt. Wait for DNS; Caddy requests HTTPS automatically.
8. Verify operator login, unauthenticated denial, payment capture, governed read, saved recommendation, exact operator execution, provider receipt, duplicate rejection and AgntID reporting. Confirm data survives a container restart.

Hosted mode blocks direct-agent and replay execution routes. Secrets and payment MCP are private to Docker. Existing local demo stays available. This is an authenticated single-operator TEST deployment, not a multi-tenant production payment system. Manual reconciliation remains required for uncertain outcomes. Domain setup, cloud capacity, ARM compatibility, image pull/build and live checks are pending.
