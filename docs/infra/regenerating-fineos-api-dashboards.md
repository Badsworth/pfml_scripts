# Regenerating Fineos API Dashboards

Fineos API dashboards have been generated programmatically in New Relic. In the future, we should update these dashboards in code rather than through the UI.

## Updating the Code

The dashboard generation code lives in [`/e2e/src/scripts/2021-07-19-generate-nr-api-dashboards.ts`](/e2e/src/scripts/2021-07-19-generate-nr-api-dashboards.ts). Make your changes to the queries in that file.

## Regenerating the dashboards

Dashboards for each environment may be regenerated using this process:

1. Create an `e2e/.env` file if you don't have one. Inside that file, you will need at least  a `NEWRELIC_APIKEY` and a `NEWRELIC_ACCOUNTID`. The `NEWRELIC_APIKEY` is a "User" key for your user in New Relic. The `NEWRELIC_ACCOUNTID` is PFML's NR Account ID (currently `2837112`).
2. Install E2E dependencies:
    ```shell
   cd e2e
   npm i
   ```
3. Run the dashboard update script:
    ```shell
    npm run newrelic:generate-fineos-dashboards
    ```

This will push an update to each of the dashboards.
