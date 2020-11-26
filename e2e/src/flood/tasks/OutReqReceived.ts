import { Locator, Browser, By } from "@flood/element";
import {
  waitForElement,
  waitForRealTimeSim,
  isFinanciallyEligible,
} from "../helpers";
import {
  TaskType,
  StoredStep,
  LSTSimClaim,
  StandardDocumentType,
  standardDocuments,
} from "../config";
import Tasks from "./index";
import { approveEvidence } from "./ApproveClaim";

let taskDescription: string;
const attachedDocuments: StandardDocumentType[] = [];
const missingDocuments: StandardDocumentType[] = [];

export const taskName: TaskType = "Outstanding Requirement Received";

export const PreORR = async (browser: Browser): Promise<void> => {
  const description = await waitForElement(
    browser,
    By.css(".ListRowSelected td[id*='workqueuelistviewDescription']")
  );
  taskDescription = await description.text();

  const openTask = await waitForElement(
    browser,
    By.css('a[aria-label="Open Task"]')
  );
  await browser.click(openTask);

  const openClaim = await waitForElement(
    browser,
    By.css('a[title="Navigate to case details"]')
  );
  await browser.click(openClaim);
};

export default async (browser: Browser, data: LSTSimClaim): Promise<void> => {
  // check if claim has already been approved or declined
  const claimStatus = await (
    await waitForElement(browser, By.css(".key-info-bar .status"))
  ).text();
  // go to the absence hub tab
  const absenceHubTab = await waitForElement(
    browser,
    By.css("[class^='TabO'][keytipnumber='5']")
  );
  await browser.click(absenceHubTab);
  let evidenceStatus = "Not Satisfied";
  if (claimStatus.includes("Adjudication")) {
    // check evidence status if claim's in adjudication
    evidenceStatus = await (
      await waitForElement(
        browser,
        By.css("td[id*='leavePlanAdjudicationListviewWidgetEvidenceStatus0']")
      )
    ).text();
    // go to the documents tab
    // make inventory of attached documents
    const documentsTab = await waitForElement(
      browser,
      By.css("[class^='TabO'][keytipnumber='11']")
    );
    await browser.click(documentsTab);
    for (const docType of standardDocuments) {
      // check if the document is there and keep track
      try {
        const document: Locator = By.css(`a[title='${docType}' i]`);
        await waitForElement(browser, document);
        attachedDocuments.push(docType);
      } catch (e) {
        missingDocuments.push(docType);
      }
    }
  }
  // if claim is not in adjudication,
  // or evidence is not valid
  // or there are no documents to review
  if (
    !claimStatus.includes("Adjudication") ||
    evidenceStatus.includes("Not Satisfied") ||
    attachedDocuments.length === 0
  ) {
    // close task
    console.info("Claim or Evidence is not reviewable. Closing task...");
    await steps[steps.length - 1].test(browser, data);
    return;
  }
  // verify eligibility before continuing
  const isEligible = await isFinanciallyEligible(browser);
  if (isEligible) {
    for (const step of steps) {
      console.info(`Outstanding Requirement Received - ${step.name}`);
      await step.test(browser, data);
    }
  } else {
    // Deny claim due to Lack of Financial Eligibility
    await Tasks.Deny(browser, data);
  }
};

export const steps: StoredStep[] = [
  {
    name: "Review documents received",
    test: async (browser: Browser, data: LSTSimClaim): Promise<void> => {
      // go to the documents tab
      const documentsTab = await waitForElement(
        browser,
        By.css("[class^='TabO'][keytipnumber='11']")
      );
      await browser.click(documentsTab);
      // open documents & review
      for (const docType of attachedDocuments) {
        const document: Locator = By.css(`a[title='${docType}' i]`);
        const popupPage = await browser.page;
        await browser.click(document);
        const documentPage = await browser.waitForNewPage();
        await browser.wait(5000);
        documentPage.close({ runBeforeUnload: true });
        await browser.switchTo().page(popupPage);
      }
      await waitForRealTimeSim(browser, data, 1 / steps.length);
    },
  },
  {
    name: "Approve evidence received",
    test: async (browser: Browser, data: LSTSimClaim): Promise<void> => {
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
      if (missingDocuments.length > 0) {
        // if documents are missing
        for (const missingDocument of missingDocuments) {
          data.missingDocument = missingDocument;
          await Tasks.PreRequestAdditionalInfo(browser, data);
          await Tasks.RequestAdditionalInformation(browser, data);
        }
      }
      // if documents exist, approve evidence
      await approveEvidence.test(browser, data);

      const okButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='OK']")
      );
      await browser.click(okButton);
      await waitForRealTimeSim(browser, data, 1 / steps.length);
    },
  },
  {
    name: "Close ORR Task",
    test: async (browser: Browser, data: LSTSimClaim): Promise<void> => {
      // go to the tasks tab
      const tasksTab = await waitForElement(
        browser,
        By.css("[class^='TabO'][keytipnumber='9']")
      );
      await browser.click(tasksTab);
      // find this task
      const currentTask = await waitForElement(
        browser,
        By.css(`table[id*='TasksForCaseWidget'] td[title='${taskDescription}']`)
      );
      await browser.click(currentTask);
      // close this task
      const closeTaskButton = await waitForElement(
        browser,
        By.css("input[title='Close selected task']")
      );
      await browser.click(closeTaskButton);
      await waitForRealTimeSim(browser, data, 1 / steps.length);
    },
  },
];
