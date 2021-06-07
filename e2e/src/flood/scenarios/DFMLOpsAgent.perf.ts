import Agent from "./Agent";
import {
  globalElementSettings as settings,
  TaskType,
  LSTScenario,
} from "../config";

export const scenario: LSTScenario = "DFMLOpsAgent";
export const tasksToDo = 1;
export const actions: TaskType[] = [];

const { default: DFMLOpsAgent, steps } = Agent(scenario);
export { settings, steps };
export default DFMLOpsAgent;
