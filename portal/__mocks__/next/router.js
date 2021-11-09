import { mockRouter, mockRouterEvents } from "../../lib/mock-helpers/router";
export * from "../../lib/mock-helpers/router";

afterEach(() => {
  mockRouter.pathname = "";

  // Clear mock router events
  mockRouterEvents.length = 0;
});
