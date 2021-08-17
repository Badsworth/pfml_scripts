#
# Dockerfile for creating image
# to run LST in AWS Fargate
# 
FROM mcr.microsoft.com/playwright:v1.10.0-bionic
WORKDIR /e2e
ENV CYPRESS_INSTALL_BINARY=0
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=1
ENV PLAYWRIGHT_SKIP_BROWSER_GC=1
COPY package*.json ./
RUN npm ci
COPY ./ ./
RUN E2E_ENVIRONMENT=test npm run artillery:bundle
CMD node_modules/.bin/artillery run -e test -q dist/spec.yml
