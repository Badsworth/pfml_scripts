import { Browser, By } from "@flood/element";
import { StoredStep } from "../config";
import { waitForElement, labelled } from "../helpers";

export const steps: StoredStep[] = [
  {
    name: "Reject leave plan",
    test: async (browser: Browser): Promise<void> => {
      const rejectPlan = await waitForElement(
        browser,
        By.css("input[type='submit'][value='Reject']")
      );
      await rejectPlan.click();
    },
  },
  {
    name: "Deny application",
    test: async (browser: Browser): Promise<void> => {
      const denyButton = await waitForElement(
        browser,
        By.css("a[aria-label='Deny']")
      );
      await denyButton.click();

      const reasonSelect = await labelled(browser, "Denial Reason");
      await browser.selectByText(reasonSelect, "Fully Denied");

      const notesInput = await labelled(browser, "Notes");
      await browser.type(notesInput, "Denied by PFML for LST purposes.");
      /* 
      const okButton = await waitForElement(
        browser,
        By.css("[id*='Popup'] input[type='submit'][value='OK']")
      );
      await okButton.click();
      */
      await waitForElement(browser, By.visibleText("Declined"));
    },
  },
];

export default async (browser: Browser, data: unknown): Promise<void> => {
  for (const step of steps) {
    console.log(`Deny - ${step.name}`);
    await step.test(browser, data);
  }
};
