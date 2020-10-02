import { TestData, StepFunction, Browser, step, By } from "@flood/element";
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
  let taskTypeElementLocator = By.css(taskTypeElementSelectors.join(", "));

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

        // this is mostly for testing purposes,
        // forces script to run the task type specified in claims.json
        const _data = data as SimulationClaim & { priorityTask: string };
        if ("priorityTask" in _data) {
          taskTypeElementLocator = By.css(`td[title="${_data.priorityTask}"]`);
          tasksToDo = 1;
        }
        // start doing a task
        await doNextTask(browser, data);
      },
    },
  ];

  async function doNextTask(browser: Browser, data: unknown): Promise<void> {
    // select a task
    const nextTask = await waitForElement(browser, taskTypeElementLocator);
    const nextTaskType = await nextTask.text();
    await nextTask.click();

    // click do task
    const doTask = await waitForElement(
      browser,
      By.css('a[aria-label="Do Task"]')
    );
    await doTask.click();

    // Waits for new window tab to load
    // and changes browser focus to that new tab
    await browser.wait(5000);
    const page = await browser.waitForNewPage();
    await browser.switchTo().page(page);
    await browser.setViewport({ width: 1280, height: 1024 });

    // Runs task-specific handler
    await taskTypes[nextTaskType](browser, data);

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
