import Agent from "./Agent";
import {
  globalElementSettings as settings,
  TaskType,
  LSTScenario,
} from "../config";

export const scenario: LSTScenario = "SavilinxAgent";
export const tasksToDo = 1;
export const actions: TaskType[] = [
  "Adjudicate Absence",
  "ID Review",
  "Certification Review",
];

const { default: SavilinxAgent, steps } = Agent(scenario);
export { settings, steps };
export default SavilinxAgent;
