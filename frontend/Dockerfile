# ---- Stage 1: Build ----
FROM node:20-alpine AS build

WORKDIR /app

# Enable pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy dependency files
COPY package.json pnpm-lock.yaml ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy app source
COPY . .

# Build Vite app
ENV VITE_API_URL=http://localhost:8080
RUN pnpm run build


# ---- Stage 2: Serve ----
FROM node:20-alpine AS production

WORKDIR /app

# Enable pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy built app
COPY --from=build /app/dist ./dist

# Expose Vite port
EXPOSE 5173

# Default ENV (can override)
ENV VITE_API_URL=http://localhost:8080

# Use npx to run serve directly
CMD ["npx", "serve", "-s", "dist", "-l", "5173"]
