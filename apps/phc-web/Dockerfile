# phc-web (Next.js standalone) for Cloud Run.
# Build context = the repository root (pnpm workspace) or the minimal staged copy made by
# infrastructure/cloud-run/deploy.sh:  docker build -f apps/phc-web/Dockerfile .
# NEXT_PUBLIC_* values are inlined at build time. They come from apps/phc-web/.env.production, which the deploy
# script generates in the (temporary, never committed) build context.
FROM node:22-slim AS build
ENV PNPM_HOME=/pnpm PATH=/pnpm:$PATH NEXT_TELEMETRY_DISABLED=1
RUN corepack enable
WORKDIR /repo
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/phc-web/package.json apps/phc-web/
RUN pnpm install --frozen-lockfile --filter phc-web...
COPY apps/phc-web apps/phc-web
RUN pnpm --filter phc-web build

FROM node:22-slim
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=8080 HOSTNAME=0.0.0.0
WORKDIR /app
COPY --from=build --chown=node:node /repo/apps/phc-web/.next/standalone ./
COPY --from=build --chown=node:node /repo/apps/phc-web/.next/static ./apps/phc-web/.next/static
COPY --from=build --chown=node:node /repo/apps/phc-web/public ./apps/phc-web/public
USER node
CMD ["node", "apps/phc-web/server.js"]
