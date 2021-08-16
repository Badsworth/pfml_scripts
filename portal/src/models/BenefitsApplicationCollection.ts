import BaseCollection from "./BaseCollection";
import { BenefitsApplicationStatus } from "./BenefitsApplication";

/** @typedef {import('./BenefitsApplication').default} BenefitsApplication */

export default class BenefitsApplicationCollection extends BaseCollection {
  get idProperty() {
    return "application_id";
  }

  /**
   * @returns {BenefitsApplication[]} Returns all claims with an "Started" or "Submitted" status
   */
  get inProgress() {
    return this.items.filter(
      (item) => item.status !== BenefitsApplicationStatus.completed
    );
  }

  /**
   * @returns {BenefitsApplication[]} Returns all claims submitted to the API, including
   * those that made it to the Claims Processing System
   */
  get submitted() {
    return this.items.filter((item) => item.isSubmitted);
  }

  /**
   * @returns {BenefitsApplication[]} Returns all claims that have completed all parts of
   the progressive application
   */
  get completed() {
    return this.items.filter((item) => item.isCompleted);
  }
}
