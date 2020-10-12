import {
  TestData,
  StepFunction,
  ElementHandle,
  Browser,
  step,
  By,
} from "@flood/element";
import { SimulationClaim } from "../../simulation/types";
import { fineosUserTypeNames, FineosUserType } from "../../simulation/types";
import { StoredStep, getFineosBaseUrl } from "../config";
import { waitForElement } from "../helpers";

export type TaskTypes = {
  [k: string]: StepFunction<unknown>;
};

export type Agent = {
  steps: StoredStep[];
  default: () => void;
};

export default (
  scenario: string,
  taskTypes: TaskTypes,
  tasksToDo = 1
): Agent => {
  let tasksDone = 0;

  const taskTypeElementSelectors: string[] = [];
  for (const key in taskTypes) {
    taskTypeElementSelectors.push(`td[title="${key}"]`);
  }
  let taskTypeElementLocator = taskTypeElementSelectors.join(", ");

  // Decides which user account to login with.
  let userType: FineosUserType | undefined;
  for (const typeName of fineosUserTypeNames) {
    if (scenario.toUpperCase().includes(typeName)) {
      userType = typeName as FineosUserType;
      break;
    }
  }
  if (typeof userType === "undefined") {
    throw new Error("Agent doesn't have a user type!");
  }

  const steps: StoredStep[] = [
    {
      name: "Login into fineos",
      test: async (browser: Browser): Promise<void> => {
        await browser.visit(await getFineosBaseUrl(userType));
      },
    },
    {
      name: "Do task",
      test: async (browser: Browser, data: unknown): Promise<void> => {
        // navigate to tasks list and find next task type
        const linkTasks = await waitForElement(
          browser,
          By.css('a[aria-label="Tasks"]')
        );
        await linkTasks.click();

        // start doing a task
        await doNextTask(browser, data);
      },
    },
  ];

  async function doNextTask(browser: Browser, data: unknown): Promise<void> {
    // this is mostly for testing purposes,
    // forces script to run the task type specified in claims.json
    const _data = data as SimulationClaim & { priorityTask: string };

    // get next task
    const getNextTask = await waitForElement(
      browser,
      By.css('a[title="Get Next Task"]')
    );
    await getNextTask.click();

    let nextTask: ElementHandle;
    try {
      nextTask = await waitForElement(browser, By.css(taskTypeElementLocator));
    } catch (e) {
      if (!("priorityTask" in _data)) throw new Error(e);
      tasksToDo = 1;
      taskTypeElementLocator = `td[title="${_data.priorityTask}"]`;
      await findClaimType(browser, data);
      nextTask = await waitForElement(browser, By.css(taskTypeElementLocator));
    }

    // select next task
    const nextTaskType = await nextTask.text();
    await nextTask.click();

    // Runs task-specific pre-hook
    const preHook = `Before ${nextTaskType}`;
    if (preHook in taskTypes) {
      await taskTypes[`Before ${nextTaskType}`](browser, data);
    }

    // do task button click opens a popup window
    const currentPage = await browser.page;
    const doTask = await waitForElement(
      browser,
      By.css('a[aria-label="Do Task"]')
    );
    await doTask.click();

    // Waits for new popup window to load
    // and change browser focus to that new tab
    await browser.wait(5000);
    const page = await browser.waitForNewPage();
    await browser.switchTo().page(page);
    await browser.setViewport({ width: 1920, height: 1080 });

    // Runs task-specific main handler
    await taskTypes[nextTaskType](browser, data);

    // Close popup window & go back to initial window
    await browser.wait(3000);
    page.close({ runBeforeUnload: true });
    await browser.switchTo().page(currentPage);
    const closeTask = await waitForElement(
      browser,
      By.css("input[type='submit'][value='Close']")
    );
    await closeTask.click();

    // Task was completed, so tasksDone += 1
    tasksDone++;

    // Continue if there are more tasks to do
    if (tasksDone < tasksToDo) {
      await doNextTask(browser, data);
    }
  }

  return {
    steps,
    default: (): void => {
      TestData.fromJSON<SimulationClaim>("../data/claims.json").filter(
        (line) => line.scenario === scenario
      );
      steps.forEach((action) => {
        step(action.name, action.test);
      });
    },
  };
};

async function findClaimType(browser: Browser, data: unknown) {
  const _data = data as SimulationClaim & { priorityTask: string };
  const departmentTasksTab = await waitForElement(
    browser,
    By.visibleText("Department Tasks")
  );
  await browser.click(departmentTasksTab);

  const filterByType = await waitForElement(
    browser,
    By.css("a[title='Filter by:TaskType']")
  );
  await browser.click(filterByType);

  let filterInput = await waitForElement(
    browser,
    By.css("#PopupContainer .filterField input[id*='_Name']")
  );
  await browser.type(filterInput, _data.priorityTask);

  let applyFilter = await waitForElement(
    browser,
    By.css(".popup_buttons input[value='Apply'][onclick*='_Name']")
  );

  await browser.click(applyFilter);

  await browser.wait(2000);

  const claimantName = `${_data.claim.first_name} ${_data.claim.last_name}`.trim();
  if (claimantName.length > 0) {
    const filterBySubject = await waitForElement(
      browser,
      By.css("a[title='Filter by:Subject']")
    );
    await browser.click(filterBySubject);

    filterInput = await waitForElement(
      browser,
      By.css("#PopupContainer .filterField input[id*='_SubjectReference']")
    );
    await browser.type(filterInput, claimantName);
  }

  applyFilter = await waitForElement(
    browser,
    By.css(".popup_buttons input[value='Apply'][onclick*='_SubjectReference']")
  );

  await browser.click(applyFilter);

  await browser.wait(2000);
}
