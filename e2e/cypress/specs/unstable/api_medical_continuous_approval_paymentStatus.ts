import { fineos, fineosPages, portal } from "../../actions";
import { ApplicationResponse } from "_api";
import {
  isToday,
  format,
  differenceInHours,
  getHours,
  isAfter,
} from "date-fns";
import { config } from "../../actions/common";
import { addBusinessDays } from "date-fns/esm";
import { convertToTimeZone } from "date-fns-timezone";
import { calculatePaymentDatePreventingOP } from "../../actions/fineos.pages";

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
          claimPage.approve("Approved", config("HAS_APRIL_UPGRADE") === "true");
          claimPage.triggerNotice("Designation Notice");
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
          if (config("HAS_FEB_RELEASE") === "true") {
            return (
              isAfter(
                new Date(),
                calculatePaymentDatePreventingOP(
                  new Date(application.updated_time)
                )
              ) && application.status === "Completed"
            );
          }
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
        // payments are only processed on weekdays, warranting the use of addBusinessDays
        const paymentDate =
          config("HAS_FEB_RELEASE") === "true"
            ? addBusinessDays(calculatePaymentDatePreventingOP(), 1) // calculatePaymentDatePreventingOP returns the processing date, a business day is added to allow payment to fully process
            : addBusinessDays(
                // Enforce using EST time
                // Causes failures if local timezone is behind EST, and claim submission time in EST is past 23:59
                convertToTimeZone(response.updated_at, {
                  timeZone: "America/New_York",
                }),
                1
              );
        // Additional pay period is included in lumpsum payment due to preventing overpayment rules
        const paymentAmount =
          config("HAS_FEB_RELEASE") === "true" ? "2493.18" : "1,662.12";
        if (config("ENVIRONMENT") !== "trn2") {
          portal.assertPaymentsOverV66([
            {
              status: `Check mailed on ${format(paymentDate, "MMMM d, yyyy")}`,
              amount: paymentAmount,
            },
          ]);
        } else {
          portal.assertPaymentsUnderV66([
            {
              paymentMethod: "Check",
              estimatedScheduledDate: "Sent",
              dateSent: format(
                addBusinessDays(
                  // Enforce using EST time
                  // Causes failures if local timezone is behind EST, and claim submission time in EST is past 23:59
                  convertToTimeZone(response.updated_at, {
                    timeZone: "America/New_York",
                  }),
                  1
                ),
                "M/d/yyyy"
              ),
              amount: paymentAmount,
            },
          ]);
        }
      });
    });
  });

  it("Provides a payment status 'Check back date' for the claimant to view payments ", () => {
    portal.before();
    portal.login(credentials);
    cy.wait("@getApplications").then(({ response }) => {
      const applications: ApplicationResponse[] = response?.body.data;
      const completedToday: ApplicationResponse[] = applications.filter(
        (application) => {
          if (!application.updated_at) throw Error("updated_at is undefined");
          // a claim cannot be older than 24 hours and must be in a completed state for this spec
          return (
            isToday(new Date(application.updated_at)) &&
            application.status === "Completed"
          );
        }
      );
      cy.task("findFirstApprovedClaim", {
        applications: completedToday,
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
        // portal/v58.0-rc2 contains updates to push back the "Check back date"
        if (
          config("ENVIRONMENT") === "stage" ||
          config("ENVIRONMENT") === "test"
        ) {
          portal.assertPaymentCheckBackDate(
            addBusinessDays(new Date(response.updated_at), 5)
          );
        } else {
          portal.assertPaymentCheckBackDate(
            addBusinessDays(new Date(response.updated_at), 3)
          );
        }
      });
    });
  });
});
