import {
  StepFunction,
  TestData,
  Browser,
  step,
  By,
  ElementHandle,
  Until,
} from "@flood/element";
import * as Cfg from "../config";
import * as Util from "../helpers";
import { Claim } from "../actions/fineos";
import { byContains } from "../helpers";

export default (scenario: Cfg.LSTScenario): Cfg.Agent => {
  // Decides which user account to login with.
  let userType: Cfg.FineosUserType | undefined;

  // Unknown compilation issue where we cannot use "Cfg.fineosUserTypeNames"
  // instead of the array of agents directly
  for (const typeName of ["SAVILINX", "DFMLOPS"]) {
    if (scenario.toUpperCase().includes(typeName)) {
      userType = typeName as Cfg.FineosUserType;
      break;
    }
  }
  if (typeof userType === "undefined") {
    throw new Error("Agent doesn't have a user type!");
  }

  const steps: Cfg.StoredStep[] = [
    {
      name: "Login into fineos",
      test: async (browser: Browser): Promise<void> => {
        await browser.visit(await Cfg.getFineosBaseUrl(userType));
      },
    },
    {
      name: "Do task",
      test: async (browser: Browser): Promise<void> => {
        // navigate to tasks list and find next task type
        const linkTasks = await Util.waitForElement(
          browser,
          By.css('a[aria-label="Tasks"]')
        );
        await linkTasks.click();
        await browser.waitForNavigation();
        // start doing a task
        await doNextTask(browser);
      },
    },
  ];

  async function doNextTask(browser: Browser): Promise<void> {
    type TaskRow = {
      name: string;
      claim: string | undefined;
      row: ElementHandle;
    };

    async function selectActiveTasks() {
      await browser.wait(Until.elementLocated(By.linkText("Choose Role")));
      await browser.click(By.linkText("Choose Role"));
      await browser.waitForNavigation();
      await browser.wait(
        Until.elementLocated(byContains(".TreeNodeElement", "SaviLinx"))
      );
      await browser.click(byContains(".TreeNodeElement", "SaviLinx"));
      await browser.wait(
        Until.elementIsVisible("input[id*=MasterMultiSelectCB_CHECKBOX]")
      );
      await browser.click("input[id*=MasterMultiSelectCB_CHECKBOX]");
      await browser.click(byContains(".ListCell", "Adjudicate Absence"));
      await browser.click("#footerButtonsBar input[value='OK']");
    }

    async function getNextTask(): Promise<TaskRow> {
      await Util.waitForElement(
        browser,
        By.css('table[id*="workqueuelistview"]')
      );
      const tasks = await browser.findElements(
        'table[id*="workqueuelistview"] > tbody > tr'
      );
      for (const row of tasks) {
        const name = await row
          .findElement("td:nth-child(5)")
          .then((e) => e?.text() ?? "Unknown");
        const claim = await row
          .findElement("td:nth-child(7)")
          .then(async (e) => {
            const fullText = (await e?.text()) ?? "";
            const match = fullText.match(/^[A-Za-z ]+: ([A-Z|\d|\-]+)$/);
            return match ? match[1] : undefined;
          });
        return { name, row, claim };
      }
      await browser.click(By.linkText("Get Next Task"));
      await browser.waitForNavigation();
      return getNextTask();
    }

    await selectActiveTasks();
    while (true) {
      const next = await getNextTask();
      const closeTask = async () => {
        await next.row.click();
        await browser
          .findElement("a[title='Close Task']")
          .then((el) => el.click());
        await browser.waitForNavigation();
      };

      // The only task we actually deal with is adjudicate absence. Every other type of task we just close out.
      // This allows us to take a claim-oriented approach - we can do all of the tasks for a given claim all at
      // once rather than needing to do a separate doc review/cert review.
      if (next.name === "Adjudicate Absence" && next.claim) {
        // With adjudications, we immediately close the task and search the case manually. This prevents us from
        // tripping over the same case multiple times, and reduces the chance of "agent overlap" if we have two
        // threads trying to pick up the next task at a time.
        await closeTask();
        console.log(`Beginning adjudication of ${next.claim}`);
        const claim = await Claim.visit(browser, next.claim);

        if ((await claim.getClaimStatus()) === "Adjudication") {
          await claim.adjudicate(async (adjudication) => {
            await adjudication.evidence(async (evidence) => {
              await evidence.approveAll();
            });
            await adjudication.certificationPeriods(async (certifications) => {
              await certifications.maybePrefill();
            });

            await adjudication.maybeApprove();
          });
          if (await claim.isApprovable()) {
            await claim.approve();
          } else {
            await claim.deny();
          }
        }

        return;
      } else {
        await closeTask();
        console.log(
          `Closed task that we don't know how to process: ${next.name}.`
        );
      }
    }
  }

  return {
    steps,
    default: async (): Promise<void> => {
      TestData.fromJSON<Cfg.LSTSimClaim>(`../data/claims.json`).filter(
        (line) => line.scenario === scenario
      );

      steps.forEach((action) => {
        step(action.name, action.test as StepFunction<unknown>);
      });
    },
  };
};
