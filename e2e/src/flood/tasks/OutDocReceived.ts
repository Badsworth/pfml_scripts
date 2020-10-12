import { ElementHandle, Locator, Browser, By } from "@flood/element";
import { SimulationClaim } from "../../simulation/types";
import { labelled, waitForElement, isFinanciallyEligible } from "../helpers";
import { StoredStep } from "../config";
import Tasks from "./index";

let docToReview: string;
let attachedDocument: ElementHandle | null;

export const steps: StoredStep[] = [
  {
    name: "Check document is attached to claim",
    test: async (browser: Browser): Promise<void> => {
      // go to the documents tab
      const documentsTab = await waitForElement(
        browser,
        By.css("[class^='TabO'][keytipnumber='11']")
      );
      await browser.click(documentsTab);

      const document: Locator = By.css(`a[title='${docToReview}' i]`);

      // open document & review
      const popupPage = await browser.page;
      await browser.click(document);
      const documentPage = await browser.waitForNewPage();
      await browser.wait(5000);
      documentPage.close({ runBeforeUnload: true });
      await browser.switchTo().page(popupPage);

      // check if the document is there # browser.maybeFindElement
      try {
        attachedDocument = await waitForElement(browser, document);
      } catch (e) {
        attachedDocument = null;
      }
    },
  },
  {
    name: "Approve evidence received",
    test: async (browser: Browser, data: unknown): Promise<void> => {
      // go to the absence hub tab
      const absenceHubTab = await waitForElement(
        browser,
        By.css("[class^='TabO'][keytipnumber='5']")
      );
      await browser.click(absenceHubTab);

      const adjudicateButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='Adjudicate']")
      );
      await browser.click(adjudicateButton);

      // go to evidence and approve
      const evidenceTab = await waitForElement(
        browser,
        By.visibleText("Evidence")
      );
      await browser.click(evidenceTab);

      if (attachedDocument === null) {
        // if document is missing
        await Tasks.PreRequestAdditionalInfo(browser, {
          ...(data as SimulationClaim),
          reviewedDocument: docToReview,
        });
        await Tasks.RequestAdditionalInformation(browser, data);
      } else {
        // if document exists, approve evidence
        const evidence = await waitForElement(
          browser,
          By.css(`td[title='${docToReview}' i]`)
        );

        if (evidence) {
          await browser.doubleClick(evidence);

          await browser.wait(1000);
          const manageButton = await waitForElement(
            browser,
            By.css("input[type='submit'][value='Manage Evidence']")
          );
          await browser.click(manageButton);

          const receiptSelect = await labelled(browser, "Evidence Receipt");
          await browser.selectByText(receiptSelect, "Received");

          const decisionSelect = await labelled(browser, "Evidence Decision");
          await browser.selectByText(decisionSelect, "Satisfied");

          const reasonInput = await labelled(
            browser,
            "Evidence Decision Reason"
          );
          await browser.type(reasonInput, "PFML - Approved for LST purposes");

          const okPopupButton = await waitForElement(
            browser,
            By.css("table[id*='Popup'] input[type='button'][value='OK']")
          );
          await browser.click(okPopupButton);
        }

        const okButton = await waitForElement(
          browser,
          By.css("input[type='submit'][value='OK']")
        );
        await browser.click(okButton);
      }
    },
  },
  {
    name: "Close task",
    test: async (browser: Browser): Promise<void> => {
      // go to the tasks tab
      const tasksTab = await waitForElement(
        browser,
        By.css("[class^='TabO'][keytipnumber='9']")
      );
      await browser.click(tasksTab);

      // close this task
      const closeTaskButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='Close']")
      );
      await browser.click(closeTaskButton);

      await browser.wait(1000);
    },
  },
];

export default async (browser: Browser, data: unknown): Promise<void> => {
  // check if already been approved or declined
  const claimStatus = await (
    await waitForElement(browser, By.css(".key-info-bar .status"))
  ).text();
  // check if this task has been done
  // go to the absence hub tab
  const absenceHubTab = await waitForElement(
    browser,
    By.css("[class^='TabO'][keytipnumber='5']")
  );
  await browser.click(absenceHubTab);
  const evidenceStatus = await (
    await waitForElement(
      browser,
      By.css("td[id*='leavePlanAdjudicationListviewWidgetEvidenceStatus0']")
    )
  ).text();
  // if claim is not in adjudication,
  // or if evidence is not valid
  if (
    !claimStatus.includes("Adjudication") ||
    evidenceStatus.includes("Not Satisfied")
  ) {
    // close task
    await steps[steps.length - 1].test(browser, data);
    return;
  }

  const isEligible = await isFinanciallyEligible(browser);
  if (isEligible) {
    for (const step of steps) {
      console.log(`Outstanding Document Received - ${step.name}`);
      await step.test(browser, data);
    }
  } else {
    // Deny claim due to Lack of Financial Eligibility
    await Tasks.Deny(browser, data);
  }
};

export const PreOutstandingDocumentReceived = async (
  browser: Browser
): Promise<void> => {
  const description = await waitForElement(
    browser,
    By.css(".ListRowSelected td[id*='workqueuelistviewDescription']")
  );
  docToReview = (await description.text()).toLowerCase();
  // figure out which document to review
  if (
    docToReview.includes("hcp form") ||
    docToReview.includes("hcp document")
  ) {
    docToReview = "State Managed Paid Leave Confirmation";
  } else {
    docToReview = "Identification Proof";
  }
  console.log(docToReview);
};
