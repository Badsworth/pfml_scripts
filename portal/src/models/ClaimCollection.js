import BaseCollection from "./BaseCollection";
import { ClaimStatus } from "./Claim";

/** @typedef {import('./Claim').default} Claim */

export default class ClaimCollection extends BaseCollection {
  get idProperty() {
    return "application_id";
  }

  /**
   * @returns {Claim[]} Returns all claims with an "Started" or "Submitted" status
   */
  get inProgress() {
    return this.items.filter((item) => item.status !== ClaimStatus.completed);
  }

  /**
   * @returns {Claim[]} Returns all claims submitted to the API, including
   * those that made it to the Claims Processing System
   */
  get submitted() {
    return this.items.filter((item) => item.isSubmitted);
  }

  /**
   * @returns {Claim[]} Returns all claims that have completed all parts of
   the progressive application
   */
  get completed() {
    return this.items.filter((item) => item.isCompleted);
  }
}
