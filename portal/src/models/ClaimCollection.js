import BaseCollection from "./BaseCollection";
import { ClaimStatus } from "./Claim";

/** @typedef {import('./Claim').default} Claim */

export default class ClaimCollection extends BaseCollection {
  get idProperty() {
    return "application_id";
  }

  /**
   * @returns {Claim[]} Returns all claims with an "In progress" status
   */
  get inProgress() {
    return this.items.filter((item) => item.status === ClaimStatus.started);
  }

  /**
   * @returns {Claim[]} Returns all claims submitted to the API, including
   * those that made it to the Claims Processing System
   */
  get submitted() {
    return this.items.filter((item) => item.isCompleted || item.isSubmitted);
  }
}
