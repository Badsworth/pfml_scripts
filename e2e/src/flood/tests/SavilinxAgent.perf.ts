import Agent from "./Agent";
import { globalElementSettings as settings, TaskType } from "../config";

export const scenario = "SavilinxAgent";
export const tasksToDo = 1;
export const actions: TaskType[] = [
  "Adjudicate Absence",
  "Outstanding Requirement Received",
];

const { default: SavilinxAgent, steps } = Agent(scenario, actions, tasksToDo);
export { settings, steps };
export default SavilinxAgent;
