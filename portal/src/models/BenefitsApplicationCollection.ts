import BenefitsApplication, {
  BenefitsApplicationStatus,
} from "./BenefitsApplication";
import BaseCollection from "./BaseCollection";

export default class BenefitsApplicationCollection extends BaseCollection<BenefitsApplication> {
  get idProperty() {
    return "application_id";
  }

  /**
   * Returns all claims with an "Started" or "Submitted" status
   */
  get inProgress() {
    return this.items.filter(
      (item) => item.status !== BenefitsApplicationStatus.completed
    );
  }

  /**
   * Returns all claims submitted to the API, including
   * those that made it to the Claims Processing System
   */
  get submitted() {
    return this.items.filter((item) => item.isSubmitted);
  }

  /**
   * Returns all claims that have completed all parts of
   the progressive application
   */
  get completed() {
    return this.items.filter((item) => item.isCompleted);
  }
}
