import { TestSettings, TestData, Browser, step, By } from "@flood/element";
import { SimulationClaim } from "../../simulation/types";
import { StoredStep } from "../config";
import { waitForElement, labelled } from "../helpers";
import { steps as MainSteps } from "./fineos.perf";

export const settings: TestSettings = {
  actionDelay: 1,
  stepDelay: 1,
  waitUntil: "visible",
  userAgent: "PFML Load Test Bot",
  description: "PFML Load Test Bot",
  screenshotOnFailure: true,
  disableCache: true,
  clearCache: true,
  clearCookies: true,
};

export const scenario = "FineosDeny";
export const steps: StoredStep[] = [
  MainSteps[0],
  MainSteps[1],
  MainSteps[2],
  {
    name: "Find application in Adjucation state",
    test: async (browser: Browser): Promise<void> => {
      const firstAdjudicationClaim = By.css(
        "table[id*='CasesForPartyListviewWidget_Party'] tr[class^='ListRow'] td[title='Adjudication']"
      );
      const row = await waitForElement(browser, firstAdjudicationClaim);
      await row.click();

      const openButton = await waitForElement(
        browser,
        By.css('input[type="submit"][value="Open"]')
      );
      await openButton.click();

      const adjudicateButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='Adjudicate']")
      );
      await adjudicateButton.click();
    },
  },
  {
    name: "Adjudicate - Reject Leave Plan",
    test: async (browser: Browser): Promise<void> => {
      const rejectButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='Reject']")
      );
      await rejectButton.click();

      const okButton = await waitForElement(
        browser,
        By.css("input[type='submit'][value='OK']")
      );
      await okButton.click();
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

      const okButton = await waitForElement(
        browser,
        By.css("[id*='Popup'] input[type='submit'][value='OK']")
      );
      await okButton.click();
    },
  },
];

export default (): void => {
  TestData.fromJSON<SimulationClaim>("../data/claims.json").filter(
    (line) => line.scenario === scenario
  );
  steps.forEach((action) => {
    step(action.name, action.test);
  });
  /* Uncomment to stop test at the end of all steps */
  /* step("Delete me pls", async (browser: Browser) => {
    await browser.wait(
      Until.elementIsVisible(By.partialVisibleText("pleasestopthanks"))
    );
  }); */
};
