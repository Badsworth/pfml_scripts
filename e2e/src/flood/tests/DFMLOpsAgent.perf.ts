import Agent from "./Agent";
import { globalElementSettings as settings, TaskType } from "../config";

export const scenario = "DFMLOpsAgent";
export const tasksToDo = 1;
export const actions: TaskType[] = [];

const { default: DFMLOpsAgent, steps } = Agent(scenario, actions, tasksToDo);
export { settings, steps };
export default DFMLOpsAgent;
