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
      if ("priorityTask" in _data) {
        taskTypeElementLocator = `td[title="${_data.priorityTask}"]`;
        await findClaimType(browser, data);
      }
      nextTask = await waitForElement(browser, By.css(taskTypeElementLocator));
    } catch (e) {
      console.info("Agent could not find tasks to do!");
      return;
    }

    // select next task
    const nextTaskType = await nextTask.text();
    await nextTask.click();

    // Runs task-specific pre-hook
    const preHook = `Before ${nextTaskType}`;
    if (preHook in taskTypes) {
      await taskTypes[preHook](browser, data);
    }

    // Runs task-specific main handler
    await taskTypes[nextTaskType](browser, data);
    console.info(`${scenario} - Do task - Task Handler Done!`);

    // Runs task-specific post-hook
    const postHook = `After ${nextTaskType}`;
    if (postHook in taskTypes) {
      await taskTypes[postHook](browser, data);
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
    default: (): void => {
      TestData.fromJSON<SimulationClaim>("../data/pilot3/claims.json").filter(
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

  const claimantName = (_data.claim && "first_name" in _data.claim
    ? `${_data.claim.first_name} ${_data.claim.last_name}`
    : ""
  ).trim();
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

    applyFilter = await waitForElement(
      browser,
      By.css(
        ".popup_buttons input[value='Apply'][onclick*='_SubjectReference']"
      )
    );
    await browser.click(applyFilter);
  }

  await browser.wait(2000);
}
