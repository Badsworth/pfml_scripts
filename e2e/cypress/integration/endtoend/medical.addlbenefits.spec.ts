import type { Application } from "../../../src/types";
import { searchForClaimInFineos, submitClaim } from "../../../src/flows";
import { getFineosBaseUrl, setFeatureFlags } from "../../../src";

describe("Submit a medical claim that involves additional benefits received", function () {
  // Set Feature Flags.
  beforeEach(setFeatureFlags);

  const addlBenefits: Application = {
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
      willUseEmployerBenefits: true,
      employerBenefitsUsed: [
        {
          kind: "accrued",
          dateStart: { month: 1, day: 1, year: 2020 },
          dateEnd: { month: 12, day: 12, year: 2020 },
        },
        {
          kind: "pfml",
          dateStart: { month: 2, day: 2, year: 2020 },
          dateEnd: { month: 1, day: 1, year: 2021 },
          amount: 500,
        },
      ],
      willReceiveOtherIncome: true,
      otherIncomeSources: [
        {
          type: "unemployment",
          dateStart: { month: 1, day: 1, year: 2020 },
          dateEnd: { month: 12, day: 12, year: 2020 },
        },
        {
          type: "selfEmp",
          dateStart: { month: 2, day: 2, year: 2020 },
          dateEnd: { month: 1, day: 1, year: 2021 },
        },
      ],
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
    cy.generateIdVerification(addlBenefits).then((applicationWithIdentity) => {
      cy.generateHCPForm(applicationWithIdentity).then((application) => {
        cy.wrap(application).as("application");
      });
    });
  });

  it("As a claimant, I should be able to submit a claim through the portal.", function () {
    submitClaim(this.application, (claimId) => {
      cy.stash("claimId", claimId);
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
