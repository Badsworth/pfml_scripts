import { Before } from "cypress-cucumber-preprocessor/steps";
import { portal, fineos } from "./actions";
import "@rckeller/cypress-unfetch/await";

Before({ tags: "@portal" }, () => {
  // Set the feature flag necessary to see the portal.

  portal.setCookies();
});

Before({ tags: "@fineos" }, () => {
  // Set up a route we can listen to wait on ajax rendering to complete.
  fineos.listenForAjax();
});
