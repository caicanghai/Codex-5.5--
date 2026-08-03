# API Service (placeholder)

**Milestone 0: placeholder — no endpoints.**

The HTTP / OpenAPI management and integration surface. The API contract is
defined **before** implementation in [`openapi/`](./openapi).

Future responsibility:

- Expose management and integration endpoints (tenant-scoped, RBAC-enforced).
- Own API key isolation and request authorization.
- Serve the OpenAPI document as the public contract.

**Boundaries:** no direct channel transport; delegates to engines/worker.

See [`openapi/openapi.yaml`](./openapi/openapi.yaml) for the skeleton (no
endpoints in Milestone 0).
