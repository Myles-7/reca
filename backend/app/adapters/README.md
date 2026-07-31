# Infrastructure adapters

Use this package for external APIs, multiple implementations, complex response
conversion, offline/recorded substitution, or explicit license/security
boundaries. PyAlex/OpenAlex, model providers and replaceable storage/parser
interfaces belong here when adopted. Stable computational libraries do not need
an Adapter merely for abstraction purity; they may be called inside Services.

Adapters return RECA DTOs and never write business tables or advance workflow
state. M0 currently contains no formal research-service adapter.
