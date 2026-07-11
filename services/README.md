# Services

Deployable runtime services for EIOS. **Milestone 0: placeholders only.** No
service contains application logic; each directory documents its future
responsibility and boundaries.

| Service | Responsibility | Must NOT |
| ------- | -------------- | -------- |
| [`gateway`](./gateway) | Unified Channel Gateway edge; normalize to the internal envelope; verify webhooks. | Contain business rules. |
| [`api`](./api) | HTTP / OpenAPI management + integration surface. | Own transport to channels. |
| [`worker`](./worker) | Asynchronous engine and broadcast processing. | Serve HTTP endpoints. |

Shared code lives in [`../packages`](../packages); deployable app bundles in
[`../apps`](../apps); topology in [`../deployments`](../deployments).
