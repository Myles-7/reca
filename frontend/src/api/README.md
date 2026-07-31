# API integration

`generated/` is produced from OpenAPI and must not be edited manually.
`adapter/` maps generated DTOs, errors and transport details into stable UI
forms. PDF.js, TanStack Table, React Flow and other libraries consume RECA API
data through this boundary; provider-specific DTOs never bypass it.
