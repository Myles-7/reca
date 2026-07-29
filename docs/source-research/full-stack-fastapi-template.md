# Full Stack FastAPI Template source record

- Official upstream: <https://github.com/fastapi/full-stack-fastapi-template>
- Fixed source commit: `c9e70d65c74f7adda417fc8de0757207ff77514c`
- Nearest release tag: `0.10.0`; the fixed commit is 186 commits after that tag.
- License: MIT. The upstream license text is preserved at
  `vendor/licenses/full-stack-fastapi-template-LICENSE.txt`.
- Import method: controlled file-level copy from the verified, read-only local
  snapshot. Git metadata, `.env` files, caches, build output, IDE settings,
  runtime data, and the upstream root `LICENSE` were excluded.
- Git history retained in RECA: no.

The import retains the FastAPI application foundation, React/Vite/TypeScript
application, authentication and user foundation, SQLModel, Alembic, generated
OpenAPI client workflow, test tooling, Docker build files, and quality tooling.

The template Item entity, CRUD routes, frontend Item page and navigation,
Item tests, and corresponding generated API client surface were removed. The
initial migration was rebased to the retained user foundation so it does not
create the template Item table.

RECA's formal build, runtime, and tests do not read or depend on
`upstream-lab`; it is only a read-only provenance source for this import.
