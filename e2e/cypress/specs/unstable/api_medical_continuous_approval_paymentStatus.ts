import { describeIf } from "./../../util";
import { fineos, fineosPages, portal } from "../../actions";
import { ApplicationResponse } from "_api";
import { isToday, format, isAfter } from "date-fns";
import { config } from "../../actions/common";
import { addBusinessDays } from "date-fns/esm";
import { calculatePaymentDatePreventingOP } from "../../actions/fineos.pages";

// Due to weekly db refreshes, we cannot test sent payments in trn
describeIf(
  config("ENVIRONMENT") !== "training" && config("ENVIRONMENT") !== "trn2",
  "Create a new caring leave claim in FINEOS and Suppress Correspondence check",
  {},
  () => {
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
            const claimPage = fineosPages.ClaimPage.visit(
              res.fineos_absence_id
            );
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
            claimPage.approve(
              "Approved",
              config("HAS_APRIL_UPGRADE") === "true"
            );
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
            return (
              isAfter(
                new Date(),
                calculatePaymentDatePreventingOP(
                  new Date(application.updated_time)
                )
              ) && application.status === "Completed"
            );
          });
        cy.task("findClaim", {
          applications: completedApplicationsBeforeToday,
          credentials,
          spec: { hasPaidPayments: true, status: "Approved" },
        }).then(([response]) => {
          if (!response) return;
          portal.claimantGoToClaimStatus(
            response.fineos_absence_id as string,
            false
          );
          portal.viewPaymentStatus();
          // Include a buffer of 3 business days from when we expect payments to be extracted
          // this allows Cypress to test the core functionality of this feature without being
          // too dependent on payment extracts
          const bufferForPaymentExtracts = Array(3)
            .fill(
              calculatePaymentDatePreventingOP(new Date(response.created_at))
            )
            .map((val, index) => {
              // payments are only processed on weekdays, warranting the use of addBusinessDays
              return addBusinessDays(val, index + 1);
            });
          const formattedDates = bufferForPaymentExtracts
            .map((date) => format(date, "MMMM d, yyyy"))
            .join("|");
          portal.assertPayments([
            {
              status: new RegExp(`Check mailed on (${formattedDates})`),
              amount: "2,493.18",
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
          // @todo: Once https://lwd.atlassian.net/browse/PORTAL-2003 is rolled out to all lower environments the LOC below should be used:
          // portal.assertPaymentCheckBackDate(addBusinessDays(twoWeeksAfterStart, 6))
          portal.assertPaymentCheckBackDate(undefined, [
            addBusinessDays(new Date(response.updated_at), 5),
            addBusinessDays(new Date(response.updated_at), 6),
          ]);
        });
      });
    });
  }
);
