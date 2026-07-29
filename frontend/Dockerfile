# Build and preview the Vite frontend with the version locked in bun.lock.
FROM oven/bun:1.2.22

WORKDIR /app

COPY package.json bun.lock /app/

COPY frontend/package.json /app/frontend/

WORKDIR /app/frontend

RUN bun install --frozen-lockfile

COPY ./frontend /app/frontend
ARG VITE_API_URL
ARG VITE_APP_ENV
ARG VITE_DEMO_MODE

RUN bun run build


EXPOSE 5173

CMD ["bun", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
