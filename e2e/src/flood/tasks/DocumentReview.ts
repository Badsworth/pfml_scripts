import { Locator, Browser, By } from "@flood/element";
import {
  waitForElement,
  waitForRealTimeSim,
  isFinanciallyEligible,
} from "../helpers";
import {
  StoredStep,
  LSTSimClaim,
  StandardDocumentType,
  TaskType,
} from "../config";
import Tasks from "./index";
import { approveEvidence } from "./ApproveClaim";

let breakTaskFlow = false;
let breakStepFlow = false;
let taskName: TaskType;
let docType: StandardDocumentType;
let taskDescription: string;

export const PreDocumentReview = async (browser: Browser): Promise<void> => {
  const openTask = await waitForElement(
    browser,
    By.css('a[aria-label="Open Task"]')
  );
  await browser.click(openTask);

  const name = await waitForElement(browser, By.css("[id*='WorkTypeName']"));
  const description = await waitForElement(
    browser,
    By.css("span[id$='Description']")
  );
  taskName = (await name.text()) as TaskType;
  taskDescription = await description.text();
  switch (taskName) {
    case "ID Review":
      docType = "Identification Proof";
      break;
    case "Certification Review":
      docType = "State managed Paid Leave Confirmation";
      break;
    default:
      throw new Error(`Unknown document type for task: '${taskName}'.`);
  }
  try {
    const openClaim = await waitForElement(
      browser,
      By.css('a[title="Navigate to case details"]')
    );
    await browser.click(openClaim);
  } catch (e) {
    // if this task is not attached to any claim, close task
    const closeTask = await waitForElement(
      browser,
      By.css("[title='Close Task']")
    );
    await browser.click(closeTask);
    breakTaskFlow = true;
  }
};

export default async (browser: Browser, data: LSTSimClaim): Promise<void> => {
  if (breakTaskFlow) return;
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
    await browser.wait(1000);
    // check evidence status if claim's in adjudication
    evidenceStatus = await (
      await waitForElement(
        browser,
        By.css("td[id*='leavePlanAdjudicationListviewWidgetEvidenceStatus0']")
      )
    ).text();
    // go to the documents tab
    const documentsTab = await waitForElement(
      browser,
      By.css("[class^='TabO'][keytipnumber='11']")
    );
    await browser.click(documentsTab);
    // check if the document is there and keep track
    try {
      const document: Locator = By.css(`a[title='${docType}' i]`);
      await waitForElement(browser, document);
    } catch (e) {
      // in case there are no documents attached, don't throw error
      evidenceStatus = "Not Satisfied";
    }
  }
  // if claim is not in adjudication,
  // or evidence is not valid
  // or there are no documents to review
  if (
    !claimStatus.includes("Adjudication") ||
    evidenceStatus.includes("Not Satisfied")
  ) {
    // close task
    console.info(
      "\n\n\nClaim or Evidence is not reviewable. Closing task...\n\n\n"
    );
    await steps[steps.length - 1].test(browser, data);
    return;
  }
  // verify eligibility before continuing
  const isEligible = await isFinanciallyEligible(browser);
  if (isEligible) {
    for (const step of steps) {
      if (breakStepFlow) {
        console.info(
          `A breaking condition was found therefore steps after '${
            steps[steps.indexOf(step) - 1].name
          }' were not executed.`
        );
        break;
      }
      const stepName = `${taskName} - ${step.name}`;
      try {
        console.info(stepName);
        await step.test(browser, data);
        await waitForRealTimeSim(browser, data, 1 / steps.length);
      } catch (e) {
        throw new Error(`Failed to execute step "${stepName}": ${e}`);
      }
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
      try {
        const document: Locator = By.css(`a[title='${docType}' i]`);
        // const popupPage = await browser.page;
        await waitForElement(browser, document);
        // const documentPage = await browser.waitForNewPage();
        // await browser.wait(5000);
        // documentPage.close({ runBeforeUnload: true });
        // await browser.switchTo().page(popupPage);
      } catch (e) {
        breakStepFlow = true;
        data.missingDocument = docType;
        await Tasks.RequestAdditionalInformation(browser, data);
      }
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
      // if documents exist, approve evidence
      await approveEvidence(docType).test(browser, data);

      const okButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='OK']")
      );
      await browser.click(okButton);
    },
  },
  {
    name: "Close document review task",
    test: async (browser: Browser): Promise<void> => {
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
    },
  },
];
