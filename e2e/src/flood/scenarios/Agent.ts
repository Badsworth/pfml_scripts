import { StepFunction, TestData, Browser, step, By } from "@flood/element";
import * as Cfg from "../config";
import * as Util from "../helpers";

export default (
  scenario: Cfg.LSTScenario,
  actions: Cfg.TaskType[],
  tasksToDo = 1
): Cfg.Agent => {
  let tasksDone = 0;

  const taskTypeElementSelectors: string[] = [];
  for (const key of actions) {
    taskTypeElementSelectors.push(`td[title="${key}"]`);
  }
  let taskTypeElementLocator = taskTypeElementSelectors.join(", ");

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

  let loginAttempts = 0;
  const tryLogin = async (browser: Browser) => {
    try {
      await browser.visit(await Cfg.getFineosBaseUrl(userType));
    } catch (e) {
      console.info(`\n${e.originalError}\n`);
      if (loginAttempts < 5) {
        loginAttempts++;
        await tryLogin(browser);
      } else {
        console.info(
          `\n\nCannot login with "${await Cfg.getFineosBaseUrl(userType)}"!\n\n`
        );
        throw e;
      }
    }
    return;
  };

  const steps: Cfg.StoredStep[] = [
    {
      time: 0,
      name: "Login into fineos",
      test: tryLogin,
    },
    {
      time: 0,
      name: "Do task",
      test: async (browser: Browser, data: Cfg.LSTSimClaim): Promise<void> => {
        // navigate to tasks list and find next task type
        const linkTasks = await Util.waitForElement(
          browser,
          By.css('a[aria-label="Tasks"]')
        );
        await linkTasks.click();

        // start doing a task
        await doNextTask(browser, data);
      },
    },
  ];

  async function doNextTask(
    browser: Browser,
    data: Cfg.LSTSimClaim
  ): Promise<void> {
    // get next task
    await browser.waitForNavigation();
    const getNextTask = await Util.waitForElement(
      browser,
      By.css('a[title="Get Next Task"]')
    );
    await getNextTask.click();
    await browser.waitForNavigation();

    // if the agent navigated to the roles page
    const agentRole = await browser.maybeFindElement(
      By.visibleText("Choose Role and Work Subset")
    );
    if (agentRole) {
      // set new agent's role
      await browser.click(await Util.waitForElement(browser, By.css("#node")));
      await browser.waitForNavigation();
      const selectAllPermissions = await Util.waitForElement(
        browser,
        By.css("[title='Select All']")
      );
      const isChecked = await selectAllPermissions.getProperty("checked");
      if (!isChecked) {
        await browser.click(selectAllPermissions);
      }
      await browser.click(
        await Util.waitForElement(browser, By.css("input[value='OK']"))
      );
      await browser.waitForNavigation();
      // try getting a task again
      const getNextTask = await Util.waitForElement(
        browser,
        By.css('a[title="Get Next Task"]')
      );
      await getNextTask.click();
    }

    let nextTask;
    try {
      // this is mostly for testing purposes
      if ("priorityTask" in data) {
        taskTypeElementLocator = `td[title="${data.priorityTask}"]`;
        await findClaimType(browser, data);
      }
      nextTask = await Util.waitForElement(
        browser,
        By.css(taskTypeElementLocator)
      );
    } catch (e) {
      console.info("\n\n\nAgent could not find tasks to do!\n\n\n");
      return;
    }

    // select next task
    const nextTaskType = (await nextTask.text()) as Cfg.TaskType;
    await nextTask.click();
    data.agentTask = nextTaskType;

    const agentHooks: Cfg.TaskHook[] = ["Before", "", "After"];
    for (const hook of agentHooks) {
      const hookHandler = `${hook} ${nextTaskType}`.trim();
      if (hookHandler in Cfg.agentActions) {
        console.info(`\n${scenario} - ${hookHandler}\n`);
        await Cfg.agentActions[hookHandler](browser, data);
      }
    }

    // Task was completed, so tasksDone += 1
    tasksDone++;

    // Continue if there are more tasks to do
    if (tasksDone < tasksToDo) {
      await doNextTask(browser, data);
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

async function findClaimType(browser: Browser, data: Cfg.LSTSimClaim) {
  if (!data.priorityTask) return;
  const filterByType = await Util.waitForElement(
    browser,
    By.css("a[title='Filter by:TaskType']")
  );
  await browser.click(filterByType);

  let filterInput = await Util.waitForElement(
    browser,
    By.css("#PopupContainer .filterField input[id*='_Name']")
  );
  await browser.type(filterInput, data.priorityTask);

  let applyFilter = await Util.waitForElement(
    browser,
    By.css(".popup_buttons input[value='Apply'][onclick*='_Name']")
  );

  await browser.click(applyFilter);

  await browser.wait(2000);

  const claimantName = (data.claim && "first_name" in data.claim
    ? `${data.claim.first_name} ${data.claim.last_name}`
    : ""
  ).trim();
  if (claimantName.length > 0) {
    const filterBySubject = await Util.waitForElement(
      browser,
      By.css("a[title='Filter by:Subject']")
    );
    await browser.click(filterBySubject);

    filterInput = await Util.waitForElement(
      browser,
      By.css("#PopupContainer .filterField input[id*='_SubjectReference']")
    );
    await browser.type(filterInput, claimantName);

    applyFilter = await Util.waitForElement(
      browser,
      By.css(
        ".popup_buttons input[value='Apply'][onclick*='_SubjectReference']"
      )
    );
    await browser.click(applyFilter);
  }

  await browser.wait(2000);
}
