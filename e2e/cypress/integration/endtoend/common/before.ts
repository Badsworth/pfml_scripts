import { Before } from "cypress-cucumber-preprocessor/steps";
import { setFeatureFlags, catchStatusError } from "@/index";
import "@rckeller/cypress-unfetch/await";

Before({ tags: "@setFeatureFlags" }, () => setFeatureFlags());
Before({ tags: "@catchStatusError" }, () => catchStatusError());
Before({ tags: "@routeRequest" }, () =>
  cy
    .route({
      method: "POST",
      url:
        "https://paidleave-api-stage.mass.gov/api/v1/applications/*/submit_application",
    })
    .as("submitClaimResponse")
);
