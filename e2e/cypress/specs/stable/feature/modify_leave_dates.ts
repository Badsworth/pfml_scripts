import { getFineosBaseUrl } from "../../../config";
import { beforeFineos } from "../../../tests/common/before";
import { Submission } from "../../../../src/types";
import { fineos } from "../../../tests/common/actions";
import { subDays, format } from "date-fns";

describe("Leave Dates can be modified for an already submitted claim", () => {
  it(
    "Should allow CSR modification of a claim that was submitted via the Portal",
    { baseUrl: getFineosBaseUrl() },
    () => {
      beforeFineos();
      cy.visit("/");

      cy.task("generateClaim", {
        claimType: "BHAP1",
        employeeType: "financially eligible",
      }).then((claim: SimulationClaim) => {
        cy.task("submitClaimToAPI", claim).as("submission");
      });

      // Request for additional Info in Fineos
      cy.get<Submission>("@submission").then((submission) => {
        fineos.visitClaim(submission.fineos_absence_id);
        cy.get('.date-wrapper span[id*="leaveStartDate"]')
          .invoke("text")
          .as("previousStartDate");

        cy.get("input[type='submit'][value='Adjudicate']").click();
        cy.get<string>("@previousStartDate").then((dateString) => {
          const newStartDate = subDays(new Date(dateString), 1);
          fineos.changeLeaveStart(newStartDate);
          cy.wrap(newStartDate).as("newStartDate");
        });

        fineos.clickBottomWidgetButton("OK");
        cy.get<Date>("@newStartDate").then((date) => {
          cy.get('.date-wrapper span[id*="leaveStartDate"]').should(
            "have.text",
            format(date, "MM/dd/yyyy")
          );
        });
      });
    }
  );
});
