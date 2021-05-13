import { Browser, By } from "@flood/element";
import * as Cfg from "../config";
import * as Util from "../helpers";

export const taskName: Cfg.TaskType = "_ReqAddInfo";
export default async (
  browser: Browser,
  data: Cfg.LSTSimClaim
): Promise<void> => {
  data.agentTask = taskName;
  for (const step of steps) {
    const stepName = `Request Additional Info - ${step.name} - ${data.missingDocument}`;
    try {
      console.info(stepName);
      await step.test(browser, data);
    } catch (e) {
      throw new Error(`Failed to execute step "${stepName}": ${e}`);
    }
  }
};

export const steps: Cfg.StoredStep[] = [
  {
    name: "Add info for missing document",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      // go to evidence and approve
      const evidenceTab = await Util.waitForElement(
        browser,
        By.visibleText("Evidence")
      );
      await browser.click(evidenceTab);
      // start adding additional information
      const additionalInfoButton = await Util.waitForElement(
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

      const docCheckbox = await Util.waitForElement(
        browser,
        By.css(`[controlsgroup*='${documentCheckbox}'][type='checkbox']`)
      );
      await browser.click(docCheckbox);

      const notesTextarea = await Util.waitForElement(
        browser,
        By.css("textarea[id*='missingInformationBox']")
      );
      await browser.type(
        notesTextarea,
        `PFML LST missing '${data.missingDocument}'`
      );

      const okEvidenceButton = await Util.waitForElement(
        browser,
        By.css("input[type='submit'][value='OK']")
      );
      await browser.click(okEvidenceButton);

      const okButton = await Util.waitForElement(
        browser,
        By.css("input[type='submit'][value='OK']")
      );
      await browser.click(okButton);
    },
  },
  {
    name: "Add Leave Request Review notes",
    test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
      // go to the absence hub tab
      const absenceHubTab = await Util.waitForElement(
        browser,
        By.css("[class^='TabO'][keytipnumber='5']")
      );
      await browser.click(absenceHubTab);

      // go to notes tab
      const notesTab = await Util.waitForElement(
        browser,
        By.css("[class^='TabO'][keytipnumber='12']")
      );
      await browser.click(notesTab);

      const createNewButton = await Util.waitForElement(
        browser,
        By.visibleText("Create New")
      );
      await browser.click(createNewButton);

      const leaveRequestOption = await Util.waitForElement(
        browser,
        By.css("a[title='Add Leave Request Review']")
      );
      await browser.click(leaveRequestOption);

      const reviewNotesTextarea = await Util.labelled(browser, "Review note");
      await browser.type(
        reviewNotesTextarea,
        `PFML LST reviewed '${data.missingDocument}'`
      );

      const okButton = await Util.waitForElement(
        browser,
        By.css("[title*='Submit the information and close the popup']")
      );
      await browser.click(okButton);
    },
  },
];
