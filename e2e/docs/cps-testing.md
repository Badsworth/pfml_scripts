CPS Testing - Cypress Testing
========================================

## What available to use for CPS testing?
In each of the folders under `specs` we have following test that will test following items:

`ingored/cps-sp`

**fineos_intake_template** - This template will take you through the FINEOS intake process and create a claim from there.
In the claim you can adjust to test for just regular FINEOS intake process or check for CPS-906 testing.

**finoes_tasks_docs_tabs_template** - This template includes CPS-906 testing. It will submit a claim through the API and check for different things in the Tasks/Documents tabs.

**portal_api_template** - This will submit a claim through the Portal and check the claim in Fineos for the NTN #. We have the ability in the template to "Approve" the claim.
To determined what the claim or leave period that Portal will take you must go [here](/src/scenarios/cypress). A `CPS_SP` scenario will be available to make changes needed for the test. Read the @todo and uncomment or comment code.

`stable/unstable`

We have a mixture of pieces of things we tested from previous CPS releases that were added to the stable/unstable cypress test.

## How to use what is available for CPS testing?

The template can be changed in different ways either by the scenario or right within the template.
The **fineos_intake_template** has most of the changes directly in the template itself. Each template should have notes on what to do.

You have few options while testing by adding `cy.pause()` to stop the test at certain spot. If you add `cy.screenshot()` it will take a screenshot and drop under the `cypress/screenshots` folder.

Example of using pause and screenshot in a test:
```angular2html
cy.unstash<Submission>("submission").then((submission) => {
        const claimPage = fineosPages.ClaimPage.visit(
          submission.fineos_absence_id
        );
        cy.pause();
        claimPage.withdraw();
        cy.screenshot();
        claimPage.triggerNotice("Leave Request Withdrawn");
        cy.screenshot();
        claimPage.documents((docsPage) => {
          docsPage.assertDocumentExists("Pending Application Withdrawn");
          cy.screenshot();
        });
      });
```

# CPS-906 tickets and where they can be tested?

What tickets from CPS-906 were included:

| Ticket #               | Test name                                          | Leave Type             | Leave Periods        | Notes                                                                                    |
|------------------------|----------------------------------------------------|------------------------|----------------------|------------------------------------------------------------------------------------------|
| CPS-906-A              | portal_api_template.ts                             | Any                    | Any                  | Checking O/R tab available                                                               |
| CPS-906-B              | bonding_reduced_notice_notification_approval.ts    | Any                    | Any                  | Checking SOM Designation                                                                 |
| CPS-906-C              | fineos_alerts_template.ts                          | Any                    | Any                  | Alert for specific dateae 60/90 calendar days                                            |
| CPS-906-D (CPS-794)    | fineos_intake_template.ts                          | Any                    | Any                  | Check character limit in the Case Notesing                                               |
| CPS-906-E              | fineos_alerts_template.ts                          | Care for Family Member | Any                  | Alert for a Self Employed Employee                                                       |
| CPS-906-F              | fineos_alerts_template.ts                          | Any                    | Any                  | Alert for Terminated/Retired/Former Employee                                             |
| CPS-906-G (CPS-2449)   | fineos_intake_template.ts                          | Bonding                | Reduced/Intermittent | Check the Restriction in the Adjudicate                                                  |
| CPS-906-H-0 (CPS-2449) | fineos_intake_template.ts                          | Any                    | Any                  | Checking for the Identification Proof in Plan Evidence                                   |
| CPS-906-H-1 (CPS-2449) | fineos_intake_template.ts                          | Any                    | Any                  | Checking all Leave Types for Minimum Increment to does not apply                         |
| CPS-906-I              | fineos_appeal_denial_decision.ts                   | Any                    | Any                  | Adding Appeals through the Sub Case in Absence Case                                      |
| CPS-906-J (CPS-1105)   | fineos_tasks_docs_tabs_template.ts                 | Any                    | Any                  | Checking the document folder structure (Inbound, Outbound, and eForms)                   |
| CPS-906-K (CPS-1864)   | fineos_tasks_docs_tabs_template.ts                 | Any                    | Any                  | Checking multiple TaskType for SLA working days                                          |
| CPS-906-N              | caring_continous_approval_payment_ownership_90k.ts | Any                    | Any                  | Checking the Paid Leave Case routing ownership assigned to DFML Program Integrity        |
| CPS-906-O (CPS-1328)   | fineos_tasks_docs_tabs_template.ts                 | Any                    | Any                  | Checking for "Additional Information" and 9 working days                                 |
| CPS-906-P (CPS-1650)   | fineos_intake_template.ts                          | Any                    | Any                  | Checking an alert for Hours Worked Per Week (HWPW) equals 0 or NULL                      |
| CPS-906-T              | fineos_tasks_docs_tabs_template.ts                 | Any                    | Any                  | Check for "Certification Overdue Notification" not showing                               |
| CPS-906-U              | fineos_tasks_docs_tabs_template.ts                 | Any                    | Any                  | Check for "Additional Information Review" not showing                                    |
| CPS-906-V (CPS-2454)   | fineos_intake_template.ts                          | Bonding                | Any                  | Check the Plan Evidence decision is pending                                              |
| CPS-906-W (CPS-2405)   | fineos_tasks_docs_tabs_template.ts                 | Any                    | Any                  | Checking the inbound form for forms                                                      |
| CPS-906-X (CPS-2408)   | fineos_tasks_docs_tabs_template.ts                 | Any                    | Any                  | Check for multiple ID Proof in the document directory                                    |
| CPS-906-AA (CPS-2579)  |                                                    | Any                    | Any                  | Check the Work Pattern is populated alert for the Work Absence Detail in the Intake form |
