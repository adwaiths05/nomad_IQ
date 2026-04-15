FROM node:22-alpine

# Use Corepack to manage pnpm version automatically
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

# Copy dependency files first to utilize Docker layer caching
COPY package.json pnpm-lock.yaml ./

# Install dependencies (this stays cached unless package files change)
RUN pnpm install --frozen-lockfile

# Copy the rest of the source code (will skip node_modules due to .dockerignore)
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1

EXPOSE 3000

# Use pnpm dev for live-reloading during development
CMD ["pnpm", "dev", "--hostname", "0.0.0.0", "--port", "3000"]