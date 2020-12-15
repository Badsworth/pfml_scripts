import { portal } from "./actions";
import { Then } from "cypress-cucumber-preprocessor/steps";
import { CypressStepThis } from "../../../src/types";
import { fineos } from "./actions";
import { format } from "date-fns";

Then("I should see a success page confirming my claim submission", function () {
  cy.url({ timeout: 20000 }).should("include", "/applications/success");
});

Then("I should be able to return to the portal dashboard", function () {
  portal.goToDashboard();
});

Then(
  "I should be able to confirm claim was submitted successfully",
  function () {
    portal.confirmClaimSubmissionSucces();
  }
);

/**
 * Assert the data matches previously filled info
 */
Then("I should see any previously entered data", function (
  this: CypressStepThis
): void {
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  const { application } = this;
  cy.get('input[name="first_name"]').should(
    "have.value",
    application.first_name
  );
  cy.get('input[name="last_name"]').should("have.value", application.last_name);
  cy.contains("button", "Save and continue").click();
});

/**
 * Find claim in Fineos.
 *
 * @param claimId The Claim ID, as reported from the portal.
 */
Then("I should find their claim", function () {
  // Fetch the claimId from the previous step, then use it in submission to Fineos.
  cy.unstash("claimId").then((claimId) => {
    if (typeof claimId !== "string") {
      throw new Error("Invalid Claim ID from previous test.");
    }
    // cy.get(`[title="PFML API ${claimId}"]`).click();
    cy.get(`[title="Adjudication"]`).click();
    // For now, we're stopping at asserting that the claim made it to Fineos.
  });
});

/* Review Page */
Then("I should have confirmed that information is correct", function (): void {
  portal.confirmInfo();
});

/* Confirm Page */
Then(
  "I should have agreed and successfully submitted the claim",
  function (): void {
    portal.confirmSubmit();
  }
);

/* Checklist Page's reviewAndSubmit */
Then("I should review and submit the application", function (): void {
  // Usually preceeded by - "I am on the claims Checklist page"
  portal.reviewAndSubmit();
});

/* Checklist page */
// submitClaim
Then("I start submitting the claim", function (this: CypressStepThis): void {
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  const { application } = this;
  portal.selectClaimType(application);
});

Then("I have my identity verified {string}", function (
  this: CypressStepThis,
  label: string
): void {
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  const { application } = this;
  portal.verifyIdentity(application, label);
});

Then("I answer the pregnancy question", function (this: CypressStepThis) {
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  const { application } = this;
  portal.answerPregnancyQuestion(application);
});

Then("I answer the continuous leave question", function (
  this: CypressStepThis
) {
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  const { application } = this;
  portal.answerContinuousLeaveQuestion(application);
});

Then("I answer the reduced leave question", function (this: CypressStepThis) {
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  const { application } = this;
  portal.answerReducedLeaveQuestion(application);
});

Then("I answer the intermittent leave question", function (
  this: CypressStepThis
) {
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  const { application } = this;
  portal.answerIntermittentLeaveQuestion(application);
});

// enterEmployerInfo
Then("I enter employer info", function (this: CypressStepThis): void {
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  const { application } = this;
  portal.enterEmployerInfo(application);
});

Then("I enter {string} date", function (this: CypressStepThis): void {
  if (!this.application) {
    throw new Error("Application has not been set");
  }
  const { application } = this;

  portal.enterBondingDateInfo(application);
});

// reportOtherBenefits
Then("I report other benefits", function (this: CypressStepThis): void {
  portal.reportOtherBenefits();
});

// addPaymentInfo
Then("I add payment info", function (this: CypressStepThis): void {
  if (!this.paymentPreference) {
    throw new Error("Payment Preferences has not been set");
  }
  const { paymentPreference } = this;
  portal.addPaymentInfo(paymentPreference);
});

Then("I add my identity document {string}", function (
  this: CypressStepThis,
  idType: string
): void {
  portal.addId(idType);
});

Then("I add my leave certification document {string}", function (
  leaveType: string
): void {
  portal.addLeaveDocs(leaveType);
});

Then("I should add weekly wage", function (): void {
  fineos.addWeeklyWage();
});

Then("I should fufill availability request", function (): void {
  fineos.fillAvailability();
});

Then("I should confirm evidence is {string}", function (label: string): void {
  fineos.validateEvidence(label);
});

Then("I accept claim updates", function (): void {
  fineos.clickBottomWidgetButton();
});

Then("I should approve claim", function (): void {
  fineos.approveClaim();
});

Then("I should confirm {string} is not present", function (): void {
  cy.contains("No Records To Display");
});

Then("I check financial eligibility", function (): void {
  cy.get('td[title="Not Met"]');
});

Then("I click Reject", function (): void {
  fineos.clickReject();
});

Then("I should confirm task assigned to DFML Ops", function (): void {
  fineos.confirmDFMLTransfer();
});

Then("I add {string} as reason in notes", function (reason: string): void {
  let reasonText = "";
  switch (reason) {
    case "Financially Ineligible": {
      reasonText =
        "This leave claim was denied due to financial ineligibility.";
    }
    case "Insufficient Certification": {
      reasonText =
        "This leave claim was denied due to invalid out-of-state ID.";
    }
  }

  cy.get('span[id="leaveRequestDenialDetailsWidget"]')
    .find("textarea")
    .type(reasonText);
  cy.get("div[class='popup-footer']").find("input[title='OK']").click();
});

Then("I should confirm claim has been completed", function (): void {
  fineos.claimCompletion();
});

Then("I should transfer task to DMFL due to {string}", function (
  label: string
): void {
  fineos.transferToDFML(label);
});

Then("I should find the {string} document", function (label: string): void {
  fineos.findDocument(label);
});

Then("I see that financially eligibility is {string}", function (
  status: string
): void {
  cy.get("td[id*='EligibilityStatus']").contains(status);
});

Then("there should be {int} ID document(s) uploaded", function (
  count: number
): void {
  cy.contains("form", "Upload your Massachusetts driver’s license or ID card")
    .find("h3")
    .should("have.length", count);
});

Then("I should confirm the {string} notice is valid", function (
  noticeType: string
) {
  cy.unstash("claimNumber").then((id) => {
    cy.task("noticeReader", noticeType).then((data: Result) => {
      expect(data.text).to.contain(id);
    });
  });
  cy.task("deleteNoticePDF").should("equal", "Deleted Succesfully");
});

Then("I should receive a {string} notification", function (
  notificationType: string
): void {
  cy.unstash("firstName").then((firstName) => {
    cy.unstash("lastName").then((lastName) => {
      cy.unstash("dob").then((dob) => {
        cy.unstash("claimNumber").then((claimNumber) => {
          cy.unstash("employerFEIN").then((employerFEIN) => {
            if (
              !(
                typeof firstName === "string" &&
                typeof lastName === "string" &&
                typeof employerFEIN === "string"
              )
            ) {
              throw new Error("First and last name must be of type string");
            }
            // Restore this line once leave admin emails can be whitelisted
            // const tag = "employer." + employerFEIN.replace("-", "");
            const notificationRequestData = {
              notificationType: notificationType,
              recipientEmail: "gqzap.notifications@inbox.testmail.app",
              employeeName: firstName + " " + lastName,
            };
            cy.wait(180000);
            cy.task("getNotification", notificationRequestData).then(
              (emailContent) => {
                if (typeof dob !== "string") {
                  throw new Error("DOB must be a string");
                }
                dob = dob.replace(/-/g, "/").slice(5) + "/****";
                expect(emailContent.name).to.equal(firstName + " " + lastName);
                expect(emailContent.dob).to.equal(dob);
                expect(emailContent.applicationId).to.equal(claimNumber);
                if (notificationType === "employer response") {
                  expect(emailContent.url).to.equal(
                    `https://paidleave-stage.mass.gov/employers/applications/new-application/?absence_id=${claimNumber}`
                  );
                }
              }
            );
          });
        });
      });
    });
  });
});

Then(
  "I should be able to retrieve a {string} notification from testmail",
  function (notificationType: string): void {
    // this test uses notifications that have ALREADY been sent to testmail
    // this allows us to test our ability to retrieve emails, and validate data
    let firstName = "";
    let lastName = "";
    if (notificationType === "employer response") {
      firstName = "Stanford";
      lastName = "Thiel";
    } else if (notificationType === "application started") {
      firstName = "Cristian";
      lastName = "Wyman";
    } else {
      throw new Error("Notification is not a recognized type");
    }
    if (!(typeof firstName === "string" && typeof lastName === "string")) {
      throw new Error("First and last name must be of type string");
    }
    const notificationRequestData = {
      notificationType: notificationType,
      recipientEmail: "gqzap.notifications@inbox.testmail.app",
      employeeName: firstName + " " + lastName,
    };
    cy.task("getNotification", notificationRequestData).then((emailContent) => {
      expect(emailContent.name).to.equal(firstName + " " + lastName);
      if (notificationType === "employer response") {
        expect(emailContent.url).to.equal(
          `https://paidleave-stage.mass.gov/employers/applications/new-application/?absence_id=${emailContent.applicationId}`
        );
      }
    });
  }
);

Then("I add a note", function (): void {
  fineos.onTab("Notes");
  cy.contains("span", "Create New").click();
  cy.contains("a", "Leave Request Review").click();
  const reviewDate = format(new Date(), "M/d/yy");
  cy.get("table[class='WidgetPanelEditPopup']").within(() => {
    cy.get("textarea[name*='Leave_Request_Review']").type(
      `Requested revised HCP on ${reviewDate}`
    );
    cy.contains("input", "OK").click();
  });
});

Then("I continue creating the claim", function (): void {
  portal.startClaim();
  portal.onPage("start");
  portal.agreeToStart();
  portal.hasClaimId();
  portal.onPage("checklist");
});

Then("I should find the Employer Response to Leave Request", function (): void {
  cy.unstash("employerResponseComment").then((employerResponseComment) => {
    if (typeof employerResponseComment !== "string") {
      throw new Error("Comment must be a string");
    }
    fineos.findEmployerResponse(employerResponseComment);
  });
});
