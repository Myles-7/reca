# Infrastructure adapters

Use this package for external APIs, multiple implementations, complex response
conversion, offline/recorded substitution, or explicit license/security
boundaries. PyAlex/OpenAlex, model providers and replaceable storage/parser
interfaces belong here when adopted. Stable computational libraries do not need
an Adapter merely for abstraction purity; they may be called inside Services.

Adapters return RECA DTOs and never write business tables or advance workflow
state. M2 adopts PyAlex 0.21 only for OpenAlex query encoding inside
`PyAlexOpenAlexProvider`; RECA-owned `httpx` and Recorded transports enforce
timeouts, bounded retries, offline replay, Schema validation and explicit
degradation before any later Service persistence.
