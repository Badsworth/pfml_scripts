import { Browser, By } from "@flood/element";
import { StoredStep, LSTSimClaim, TaskType } from "../config";
import { labelled, waitForElement, waitForRealTimeSim } from "../helpers";

export const taskName: TaskType = "_DenyClaim";
export const steps: StoredStep[] = [
  {
    name: "Reject leave plan",
    test: async (browser: Browser): Promise<void> => {
      // go to leave details
      const leaveDetailsTab = await waitForElement(
        browser,
        By.css("[class^='TabO'][keytipnumber='6']")
      );
      await leaveDetailsTab.click();

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
      await browser.selectByText(reasonSelect, "Non-eligible employee");

      const okButton = await waitForElement(
        browser,
        By.css("[id*='Popup'] input[type='submit'][value='OK']")
      );
      await okButton.click();

      await waitForElement(browser, By.visibleText("Closed"));
    },
  },
];

export default async (browser: Browser, data: LSTSimClaim): Promise<void> => {
  data.agentTask = taskName;
  for (const step of steps) {
    const stepName = `Deny - ${step.name}`;
    try {
      console.info(stepName);
      await step.test(browser, data);
      await waitForRealTimeSim(browser, data, 1 / steps.length);
    } catch (e) {
      throw new Error(`Failed to execute step "${stepName}": ${e}`);
    }
  }
};
