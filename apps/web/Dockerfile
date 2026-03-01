FROM oven/bun:1.3.9-alpine

WORKDIR /app

COPY apps/web/package.json /app/package.json
COPY apps/web/bun.lock /app/bun.lock
COPY apps/web/tsconfig.json /app/tsconfig.json
COPY apps/web/vite.config.ts /app/vite.config.ts
COPY apps/web/index.html /app/index.html
COPY apps/web/src /app/src

RUN bun install --frozen-lockfile

EXPOSE 5173
CMD ["bun", "run", "dev", "--host", "0.0.0.0", "--port", "5173"]
