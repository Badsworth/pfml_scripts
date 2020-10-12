import { Browser, By } from "@flood/element";
import { SimulationClaim } from "../../simulation/types";
import { StoredStep } from "../config";
import { waitForElement, labelled } from "../helpers";

let reviewedDocument: string;

export const steps: StoredStep[] = [
  {
    name: "Add info for missing document",
    test: async (browser: Browser): Promise<void> => {
      // start adding additional information
      const additionalInfoButton = await waitForElement(
        browser,
        By.css("input[value='Additional Information'][type='submit']")
      );
      await browser.click(additionalInfoButton);

      let documentCheckbox = "";
      if (reviewedDocument === "Identification Proof") {
        documentCheckbox = "supportingDocumentationNotProvided";
      } else if (reviewedDocument === "State Managed Paid Leave Confirmation") {
        documentCheckbox = "healthcareProviderInformationIncomplete";
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
        `PFML LST - missing ${reviewedDocument}`
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
    test: async (browser: Browser): Promise<void> => {
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
        `PFML LST - reviewed ${reviewedDocument}`
      );

      const okButton = await waitForElement(
        browser,
        By.css("[title*='Submit the information and close the popup']")
      );
      await browser.click(okButton);
    },
  },
];

export default async (browser: Browser, data: unknown): Promise<void> => {
  for (const step of steps) {
    console.log(`Request Additional Info - ${step.name} - ${reviewedDocument}`);
    await step.test(browser, data);
  }
};

export const PreRequestAdditionalInfo = async (
  browser: Browser,
  data: unknown
): Promise<void> => {
  ({ reviewedDocument } = data as SimulationClaim & {
    reviewedDocument: string;
  });
};
