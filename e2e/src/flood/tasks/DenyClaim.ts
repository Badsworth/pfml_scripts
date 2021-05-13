import { Browser, By } from "@flood/element";
import assert from "assert";
import * as Cfg from "../config";
import * as Util from "../helpers";

export const taskName: Cfg.TaskType = "_DenyClaim";
export const steps: Cfg.StoredStep[] = [
  {
    name: "Reject leave plan",
    test: async (browser: Browser): Promise<void> => {
      // go to leave details
      const leaveDetailsTab = await Util.waitForElement(
        browser,
        By.css("[class^='TabO'][keytipnumber='6']")
      );
      await leaveDetailsTab.click();
      // reject all undecided leave plans
      await Util.waitForElement(
        browser,
        By.css("table[id*='selectedLeavePlans']")
      );
      const allLeavePlans = await browser.findElements(
        By.css("table[id*='selectedLeavePlans'] tr")
      );
      for (const leavePlan in allLeavePlans) {
        await (
          await Util.waitForElement(
            browser,
            By.css(
              `table[id*='selectedLeavePlans'] tr:nth-child(${
                parseInt(leavePlan) + 1
              })`
            )
          )
        ).click();
        const rejectPlan = await Util.waitForElement(
          browser,
          By.css("input[type='submit'][value='Reject']")
        );
        await rejectPlan.click();
        await browser.waitForNavigation();
      }
    },
  },
  {
    name: "Deny application",
    test: async (browser: Browser): Promise<void> => {
      const denyButton = await Util.waitForElement(
        browser,
        By.css("a[aria-label='Deny']")
      );
      await denyButton.click();

      const reasonSelect = await Util.labelled(browser, "Denial Reason");
      await browser.selectByText(reasonSelect, "Non-eligible employee");

      const okButton = await Util.waitForElement(
        browser,
        By.css("[id*='Popup'] input[type='submit'][value='OK']")
      );
      await okButton.click();
      await browser.waitForNavigation();

      const closed = await browser.maybeFindElement(By.visibleText("Closed"));
      const denied = await browser.maybeFindElement(By.visibleText("Denied"));
      const declined = await browser.maybeFindElement(
        By.visibleText("Declined")
      );
      assert(
        closed || denied || declined,
        "Claim was not closed/denied properly"
      );
    },
  },
];

export default async (
  browser: Browser,
  data: Cfg.LSTSimClaim
): Promise<void> => {
  data.agentTask = taskName;
  for (const step of steps) {
    const stepName = `Deny - ${step.name}`;
    try {
      console.info(stepName);
      await step.test(browser, data);
    } catch (e) {
      throw new Error(`Failed to execute step "${stepName}": ${e}`);
    }
  }
};
