import BaseCollection from "./BaseCollection";
import { BenefitsApplicationStatus } from "./BenefitsApplication";

/** @typedef {import('./BenefitsApplication').default} BenefitsApplication */

export default class BenefitsApplicationCollection extends BaseCollection {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'idProperty' in type 'BenefitsApplication... Remove this comment to see the full error message
  get idProperty() {
    return "application_id";
  }

  /**
   * @returns {BenefitsApplication[]} Returns all claims with an "Started" or "Submitted" status
   */
  get inProgress() {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'items' does not exist on type 'BenefitsA... Remove this comment to see the full error message
    return this.items.filter(
      (item) => item.status !== BenefitsApplicationStatus.completed
    );
  }

  /**
   * @returns {BenefitsApplication[]} Returns all claims submitted to the API, including
   * those that made it to the Claims Processing System
   */
  get submitted() {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'items' does not exist on type 'BenefitsA... Remove this comment to see the full error message
    return this.items.filter((item) => item.isSubmitted);
  }

  /**
   * @returns {BenefitsApplication[]} Returns all claims that have completed all parts of
   the progressive application
   */
  get completed() {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'items' does not exist on type 'BenefitsA... Remove this comment to see the full error message
    return this.items.filter((item) => item.isCompleted);
  }
}
