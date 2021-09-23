#
# Dockerfile for creating image
# to run LST in AWS Fargate
#
FROM node:lts-alpine3.14 AS builder
WORKDIR /e2e
ENV CYPRESS_INSTALL_BINARY=0
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=1
ENV PLAYWRIGHT_SKIP_BROWSER_GC=1
COPY ./package*.json ./
RUN npm ci
COPY ./ ./
RUN npm run artillery:bundle

FROM zenika/alpine-chrome:with-node
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD 1
ENV PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium-browser
WORKDIR /usr/src/app
COPY --chown=chrome --from=builder /e2e/dist/package*.json ./
RUN npm i && npm cache clean --force
COPY --chown=chrome --from=builder /e2e/dist ./dist
COPY --chown=chrome --from=builder /e2e/employees ./employees
COPY --chown=chrome --from=builder /e2e/forms ./forms
CMD node_modules/.bin/artillery run -e test dist/spec.yml
