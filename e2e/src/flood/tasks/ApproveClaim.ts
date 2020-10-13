import { Browser, By } from "@flood/element";
import { waitForElement, labelled, isFinanciallyEligible } from "../helpers";
import { StoredStep } from "../config";
import Tasks from "./index";

let evidenceApproved: boolean;

export const steps: StoredStep[] = [
  {
    name: "Check if claim is ready for approval",
    test: async (browser: Browser, data: unknown): Promise<void> => {
      // if evidence has not been reviewed yet,
      // approve all evidence
      const evidence = await waitForElement(
        browser,
        By.css("td[id*='EvidenceStatusIcon0'] i")
      );
      const evidenceIcon = await evidence.getAttribute("class");
      evidenceApproved = evidenceIcon === "icon-checkbox";

      const adjudicateButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='Adjudicate']")
      );
      await browser.click(adjudicateButton);

      if (evidenceIcon === "icon-unverified") {
        await approveEvidence.test(browser, data);
        await certifyEvidence.test(browser, data);
        evidenceApproved = true;
      }
    },
  },
  {
    name: "Paid Benefits",
    test: async (browser: Browser): Promise<void> => {
      const paidBenefitsTab = await waitForElement(
        browser,
        By.visibleText("Paid Benefits")
      );
      await browser.click(paidBenefitsTab);

      const currentAvgWeeklyAge = parseFloat(
        (
          await (
            await waitForElement(
              browser,
              By.css("[id*='paidBenefitsListviewAverageWeeklyWage0']")
            )
          ).text()
        ).replace(",", "")
      );
      console.log({ currentAvgWeeklyAge });

      if (currentAvgWeeklyAge < 1200) {
        const editButton = await waitForElement(
          browser,
          By.css("input[type='submit'][value='Edit']")
        );
        await editButton.click();

        const avgWeeklyWage = await labelled(browser, "Average weekly wage");
        await browser.clear(avgWeeklyWage);
        await browser.type(avgWeeklyWage, "1200");
        const okButton = await waitForElement(
          browser,
          By.css("input[type='submit'][value='OK']")
        );
        await browser.click(okButton);
      }
    },
  },
  {
    name: "Accept Leave Plan",
    test: async (browser: Browser, data: unknown): Promise<void> => {
      let manageRequestTab = await waitForElement(
        browser,
        By.visibleText("Manage Request")
      );
      await browser.click(manageRequestTab);

      // check if availability can still be approved
      const availabilityStatus = await (
        await waitForElement(
          browser,
          By.css("td[id*='LeaveRequestListviewWidgetAvailabilityStatus0']")
        )
      ).text();
      // when it is Pending Certification, then we can make it pass
      if (availabilityStatus === "Pending Certification") {
        const evidenceTab = await waitForElement(
          browser,
          By.visibleText("Evidence")
        );
        await evidenceTab.click();
        await certifyEvidence.test(browser, data);
      }

      // go back and try to approve leave plan
      manageRequestTab = await waitForElement(
        browser,
        By.visibleText("Manage Request")
      );
      await browser.click(manageRequestTab);
      const acceptButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='Accept']")
      );
      await browser.click(acceptButton);

      // exit adjudication
      const okButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='OK']")
      );
      await browser.click(okButton);
    },
  },
  {
    name: "Finalize claim adjudication",
    test: async (browser: Browser, data: unknown): Promise<void> => {
      // check if leave has been accepted
      const leavePlanStatus = await (
        await waitForElement(
          browser,
          By.css("td[id*='leavePlanAdjudicationListviewWidgetPlanDecision0']")
        )
      ).text();

      // if leave plan has not been accepted, deny claim
      // something was missing, most likely Availability errors
      if (leavePlanStatus !== "Accepted" || !evidenceApproved) {
        await Tasks.Deny(browser, data);
        return;
      }

      const approveButton = await waitForElement(
        browser,
        By.css("a[aria-label='Approve']")
      );
      await approveButton.click();

      await waitForElement(browser, By.visibleText("Approved"));
    },
  },
];

const approveEvidence: StoredStep = {
  name: "Evidence Review",
  test: async (browser: Browser): Promise<void> => {
    console.info("Approve - Evidence Review");
    const evidenceTab = await waitForElement(
      browser,
      By.visibleText("Evidence")
    );
    await evidenceTab.click();
    // get the list of documents attached to this claim
    const documents = await browser.findElements(
      By.css("table[id*='evidenceResultListviewWidget'] tr")
    );
    // if we have no documents to review, do nothing
    if (documents.length === 0) return;
    // approve pending documents
    for (let i = 0; i < documents.length; i++) {
      // search for this documents' review decision
      const evidence = await waitForElement(
        browser,
        By.css(
          `table[id*='evidenceResultListviewWidget'] tr:nth-child(${
            i + 1
          }) td:nth-child(5)`
        )
      );
      // if document decision is not pending, ignore
      if ((await evidence.text()) !== "Pending") continue;
      // confirmed it is pending, so we continue with approval
      await browser.doubleClick(evidence);

      await browser.wait(1000);
      const manageButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='Manage Evidence']")
      );
      await manageButton.click();

      const receiptSelect = await labelled(browser, "Evidence Receipt");
      await browser.selectByText(receiptSelect, "Received");

      const decisionSelect = await labelled(browser, "Evidence Decision");
      await browser.selectByText(decisionSelect, "Satisfied");

      const reasonInput = await labelled(browser, "Evidence Decision Reason");
      await browser.type(reasonInput, "PFML - Approved for LST purposes");

      const okButton = await waitForElement(
        browser,
        By.css("table[id*='Popup'] input[type='button'][value='OK']")
      );
      await okButton.click();
    }
  },
};
const certifyEvidence: StoredStep = {
  name: "Evidence Certification",
  test: async (browser: Browser): Promise<void> => {
    console.info("Approve - Evidence Certification");
    const certificationTab = await waitForElement(
      browser,
      By.visibleText("Certification Periods")
    );
    await certificationTab.click();

    const prefillButton = await waitForElement(
      browser,
      By.css(
        "input[type='submit'][value='Prefill with Requested Absence Periods']"
      )
    );
    await prefillButton.click();

    const yesButton = await waitForElement(
      browser,
      By.css(".popup_buttons input[type='submit'][value='Yes']")
    );
    await yesButton.click();
  },
};

export default async (browser: Browser, data: unknown): Promise<void> => {
  const isEligible = await isFinanciallyEligible(browser);
  if (isEligible) {
    for (const step of steps) {
      console.log(`Approve - ${step.name}`);
      await step.test(browser, data);
    }
  } else {
    // Deny claim due to lack of Financial Eligibility
    console.log(
      "Tried to Approve but denied claim due to lack of Financial Eligibility"
    );
    await Tasks.Deny(browser, data);
  }
};
