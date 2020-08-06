import { register } from "../../../src/flows";
import { Application } from "../../../src/types";

describe.skip("Register new account", function () {
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
  const basic: Omit<Application, "idVerification"> = {
    // @todo: For now we're submitting applications with a pre-existing user.
    // In the future we will also want to test registration flow.
    email: "rob+pfml-test-10@lastcallmedia.com",
    password: "A8kMe4NeTnG",
    firstName: "John",
    lastName: "Smith",
    dob: { month: 3, day: 31, year: 1995 },
    massId: "123",
    ssn: "123-45-6789",
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
      fein: "04-2103545",
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
        routingNumber: 123456789,
        accountNumber: 55555555,
      },
    },
  };
  it("Should be capable of registering a new account", () => {
    register(basic);
  });
});
