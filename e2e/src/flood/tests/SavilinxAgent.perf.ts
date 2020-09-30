import Tasks from "../tasks";
import Agent, { TaskTypes } from "./Agent";
import { globalElementSettings as settings } from "../config";

export const scenario = "SavilinxAgent";
export const tasksToDo = 6;
export const taskTypes: TaskTypes = {
  "Adjudicate Absence": Tasks.Adjudicate,
};

const { default: SavilinxAgent, steps } = Agent(scenario, taskTypes, tasksToDo);
export { settings, steps };
export default SavilinxAgent;
