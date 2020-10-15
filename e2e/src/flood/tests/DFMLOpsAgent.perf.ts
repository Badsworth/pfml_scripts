import Tasks from "../tasks";
import Agent, { TaskTypes } from "./Agent";
import { globalElementSettings as settings } from "../config";

export const scenario = "DFMLOpsAgent";
export const tasksToDo = 1;
export const taskTypes: TaskTypes = {
  "Tasks a dfml agent would do": Tasks.AdjudicateAbsence,
};

const { default: DFMLOpsAgent, steps } = Agent(scenario, taskTypes, tasksToDo);
export { settings, steps };
export default DFMLOpsAgent;
