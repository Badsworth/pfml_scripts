import { Browser, By } from "@flood/element";
import { StoredStep, LSTSimClaim, TaskType } from "../config";
import { waitForElement, waitForRealTimeSim, labelled } from "../helpers";

export const taskName: TaskType = "_ReqAddInfo";
export default async (browser: Browser, data: LSTSimClaim): Promise<void> => {
  data.agentTask = taskName;
  for (const step of steps) {
    const stepName = `Request Additional Info - ${step.name} - ${data.missingDocument}`;
    try {
      console.info(stepName);
      await step.test(browser, data);
      await waitForRealTimeSim(browser, data, 1 / steps.length);
    } catch (e) {
      throw new Error(`Failed to execute step "${stepName}": ${e}`);
    }
  }
};

export const steps: StoredStep[] = [
  {
    name: "Add info for missing document",
    test: async (browser: Browser, data: LSTSimClaim): Promise<void> => {
      // go to evidence and approve
      const evidenceTab = await waitForElement(
        browser,
        By.visibleText("Evidence")
      );
      await browser.click(evidenceTab);
      // start adding additional information
      const additionalInfoButton = await waitForElement(
        browser,
        By.css("input[value='Additional Information'][type='submit']")
      );
      await browser.click(additionalInfoButton);

      let documentCheckbox;
      switch (data.missingDocument) {
        case "Identification Proof":
          documentCheckbox = "supportingDocumentationNotProvided";
          break;
        case "State managed Paid Leave Confirmation":
          documentCheckbox = "healthcareProviderInformationIncomplete";
          break;
        default:
          throw new Error(`Unknown document type: '${data.missingDocument}'.`);
      }

      const docCheckbox = await waitForElement(
        browser,
        By.css(`[controlsgroup*='${documentCheckbox}'][type='checkbox']`)
      );
      await browser.click(docCheckbox);

      const notesTextarea = await waitForElement(
        browser,
        By.css("textarea[id*='missingInformationBox']")
      );
      await browser.type(
        notesTextarea,
        `PFML LST missing '${data.missingDocument}'`
      );

      const okEvidenceButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='OK']")
      );
      await browser.click(okEvidenceButton);

      const okButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='OK']")
      );
      await browser.click(okButton);
    },
  },
  {
    name: "Add Leave Request Review notes",
    test: async (browser: Browser, data: LSTSimClaim): Promise<void> => {
      // go to the absence hub tab
      const absenceHubTab = await waitForElement(
        browser,
        By.css("[class^='TabO'][keytipnumber='5']")
      );
      await browser.click(absenceHubTab);

      // go to notes tab
      const notesTab = await waitForElement(
        browser,
        By.css("[class^='TabO'][keytipnumber='12']")
      );
      await browser.click(notesTab);

      const createNewButton = await waitForElement(
        browser,
        By.visibleText("Create New")
      );
      await browser.click(createNewButton);

      const leaveRequestOption = await waitForElement(
        browser,
        By.css("a[title='Add Leave Request Review']")
      );
      await browser.click(leaveRequestOption);

      const reviewNotesTextarea = await labelled(browser, "Review note");
      await browser.type(
        reviewNotesTextarea,
        `PFML LST reviewed '${data.missingDocument}'`
      );

      const okButton = await waitForElement(
        browser,
        By.css("[title*='Submit the information and close the popup']")
      );
      await browser.click(okButton);
    },
  },
];
