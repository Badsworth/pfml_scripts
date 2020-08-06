import type { Application } from "../../../src/types";
import { submitClaim, searchForClaimInFineos } from "../../../src/flows";
import { getFineosBaseUrl, setFeatureFlags } from "../../../src";

describe("Submit a medical claim", function () {
  // Set Feature Flags.
  beforeEach(setFeatureFlags);

  const basic: Application = {
    email: Cypress.env("PORTAL_USERNAME"),
    password: Cypress.env("PORTAL_PASSWORD"),
    firstName: "Tim",
    lastName: "Cannon",
    dob: { month: 3, day: 31, year: 1995 },
    massId: "123",
    ssn: "123-45-9999",
    claim: {
      type: "medical",
      dueToPregnancy: true,
      leave: {
        type: "continuous",
        typeBasedDetails: {
          weeks: 40,
        },
        start: { month: 8, day: 1, year: 2020 },
        end: { month: 9, day: 1, year: 2020 },
      },
    },
    employer: {
      type: "employed",
      fein: "22-7777777",
      employerNotified: true,
      employerNotificationDate: { month: 7, day: 7, year: 2020 },
    },
    otherBenefits: {
      willUseEmployerBenefits: false,
      willReceiveOtherIncome: false,
      tookLeaveForQualifyingReason: false,
    },
    paymentInfo: {
      type: "ach",
      accountDetails: {
        routingNumber: 12345678,
        accountNumber: 5555555555,
      },
    },
  };

  beforeEach(() => {
    cy.generateIdVerification(basic).then((applicationWithIdentity) => {
      cy.generateHCPForm(applicationWithIdentity).then((application) => {
        cy.wrap(application).as("application");
      });
    });
  });

  it("As a claimant, I should be able to submit a claim through the portal.", function () {
    // Submit the claim, capturing the claim ID for use in the next step.
    submitClaim(this.application, (claimIdFromPortal) => {
      cy.stash("claimId", claimIdFromPortal);
    });
  });

  it(
    "As a CSR, I should be able to find the claim in Fineos",
    { baseUrl: getFineosBaseUrl() },
    function () {
      // Fetch the claimId from the previous step, then use it in submission to Fineos.
      cy.unstash("claimId").then((claimId) => {
        if (typeof claimId !== "string")
          throw new Error("Invalid Claim ID from previous test.");
        searchForClaimInFineos(this.application, claimId);
      });
    }
  );
});
