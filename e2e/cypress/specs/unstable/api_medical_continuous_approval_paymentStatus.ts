import { fineos, fineosPages, portal } from "../../actions";
import { ApplicationResponse } from "_api";
import {
  isToday,
  addDays,
  format,
  differenceInHours,
  getHours,
} from "date-fns";
import { config } from "../../actions/common";
import { addBusinessDays } from "date-fns/esm";
import { convertToTimeZone } from "date-fns-timezone";

describe("Create a new caring leave claim in FINEOS and Suppress Correspondence check", () => {
  const credentials: Credentials = {
    username: "armando+payment_status@lastcallmedia.com",
    password: config("PORTAL_PASSWORD"),
  };
  const submissionSpec = it("Checks for claim completed today", () => {
    portal.before();
    portal.login(credentials);
    cy.wait("@getApplications").then(({ response }) => {
      const filterUncompleted = (application: ApplicationResponse) =>
        application.status === "Completed";
      const completedApplications: ApplicationResponse[] =
        response?.body.data.filter(filterUncompleted);
      const submittedToday = completedApplications.some((application) =>
        isToday(new Date(application.updated_at as string))
      );
      cy.stash("hasSubmitted", submittedToday);
    });
  });

  it("CSR Rep will submit and approve claim", () => {
    cy.dependsOnPreviousPass([submissionSpec]);
    cy.unstash<boolean>("hasSubmitted").then((hasSubmitted) => {
      if (hasSubmitted) return;
      fineos.before();
      cy.task("generateClaim", "MED_CONT_ER_APPROVE").then((claim) => {
        cy.task("submitClaimToAPI", { ...claim, credentials }).then((res) => {
          cy.stash("claim", claim);
          cy.stash("submission", {
            application_id: res.application_id,
            fineos_absence_id: res.fineos_absence_id,
            timestamp_from: Date.now(),
          });
          const claimPage = fineosPages.ClaimPage.visit(res.fineos_absence_id);
          claimPage.triggerNotice("Preliminary Designation");
          fineos.onTab("Absence Hub");
          claimPage.adjudicate((adjudication) => {
            adjudication.evidence((evidence) => {
              // Receive and approve all of the documentation for the claim.
              claim.documents.forEach((document) => {
                evidence.receive(document.document_type);
              });
            });
            adjudication.certificationPeriods((certificationPeriods) =>
              certificationPeriods.prefill()
            );
            adjudication.acceptLeavePlan();
          });
          claimPage.approve("Approved").triggerNotice("Designation Notice");
        });
      });
    });
  });

  it("Displays payment information after nightly payment extract", () => {
    portal.before();
    portal.login(credentials);
    cy.wait("@getApplications").then(({ response }) => {
      const applications: ApplicationResponse[] = response?.body.data;
      const completedApplicationsBeforeToday: ApplicationResponse[] =
        applications.filter((application) => {
          if (!application.updated_time)
            throw Error("updated_time is undefined");
          // Must use EST timezone here to avoid issues when running this spec across different timezones
          // E.X running this test at 5PM PST will select a claim approved on the day the test is running, so no payments would appear
          const estTime = getHours(
            convertToTimeZone(application.updated_time, {
              timeZone: "America/New_York",
            })
          );
          // Claims approved after 1800 EST will be left out of nightly payment extracts
          const PAYMENT_BATCH_HOUR = 18;
          return (
            differenceInHours(new Date(), new Date(application.updated_time)) >
              24 &&
            estTime < PAYMENT_BATCH_HOUR &&
            application.status === "Completed"
          );
        });

      cy.task("findFirstApprovedClaim", {
        applications: completedApplicationsBeforeToday,
        credentials,
      }).then((response) => {
        if (!response) return;
        if (!response.updated_at)
          throw Error("Claim missing submission timestamp");
        portal.claimantGoToClaimStatus(
          response.fineos_absence_id as string,
          false
        );
        portal.viewPaymentStatus();
        portal.assertPayments([
          {
            paymentMethod: "Check",
            estimatedScheduledDate: "Sent",
            dateSent: format(
              addDays(new Date(response.updated_at), 1),
              "M/dd/yyyy"
            ),
            amount: "800.09",
          },
        ]);
      });
    });
  });

  it("Provides a payment status 'Check back date' for the claimant to view payments ", () => {
    portal.before();
    portal.login(credentials);
    cy.wait("@getApplications").then(({ response }) => {
      const applications: ApplicationResponse[] = response?.body.data;
      const completedApplicationsBeforeToday: ApplicationResponse[] =
        applications.filter((application) => {
          if (!application.updated_time)
            throw Error("updated_time is undefined");
          // a claim cannot be older than 24 hours and must be in a completed state for this spec
          return (
            differenceInHours(new Date(), new Date(application.updated_time)) <
              24 && application.status === "Completed"
          );
        });
      cy.task("findFirstApprovedClaim", {
        applications: completedApplicationsBeforeToday,
        credentials,
      }).then((response) => {
        if (!response) return;
        if (!response.updated_at)
          throw Error("Claim missing submission timestamp");
        portal.claimantGoToClaimStatus(
          response.fineos_absence_id as string,
          false
        );
        portal.viewPaymentStatus();
        portal.assertPaymentCheckBackDate(
          addBusinessDays(new Date(response.updated_at), 3)
        );
      });
    });
  });
});
