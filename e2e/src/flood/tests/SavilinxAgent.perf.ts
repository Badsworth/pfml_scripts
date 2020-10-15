import Tasks from "../tasks";
import Agent, { TaskTypes } from "./Agent";
import { globalElementSettings as settings } from "../config";

export const scenario = "SavilinxAgent";
export const tasksToDo = 1;
export const taskTypes: TaskTypes = {
  // Adjudicate randomly approves or denies a claim
  "Before Adjudicate Absence": Tasks.PreAdjudicateAbsence,
  "Adjudicate Absence": Tasks.AdjudicateAbsence,
  "After Adjudicate Absence": Tasks.PostAdjudicateAbsence,
  // ODR checks if certain document is added to the claim
  "Before Outstanding Document Received": Tasks.PreOutstandingDocumentReceived,
  "Outstanding Document Received": Tasks.OutstandingDocumentReceived,
};

const { default: SavilinxAgent, steps } = Agent(scenario, taskTypes, tasksToDo);
export { settings, steps };
export default SavilinxAgent;
