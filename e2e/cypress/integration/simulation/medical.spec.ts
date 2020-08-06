import { submitClaim } from "../../../src/flows";
import { generateApplication } from "../../../src/generate";

describe("Submit a medical claim", function () {
  // Set Feature Flags.
  beforeEach(() => {
    cy.setCookie(
      "_ff",
      JSON.stringify({
        pfmlTerriyay: true,
      })
    );
    cy.on("uncaught:exception", (e) => {
      // Suppress failures due to this error, which we can't do anything about.
      if (e.message.indexOf(`Cannot set property 'status' of undefined`)) {
        return false;
      }
    });
  });

  it("Submits a generated medical claim", () =>
    submitClaim(generateApplication()));
});
