import BaseModel from "./BaseModel";
import { get } from "lodash";

const fieldHasValue = (fieldPath, formState) => {
  const value = get(formState, fieldPath);

  return !!value;
};

/**
 * A model that represents a section in a user flow
 * and gives the completion status based on the current
 * state of user data
 * @returns {Step}
 */
export default class Step extends BaseModel {
  get defaults() {
    return {
      // instance of {StepDefinition}
      stepDefinition: null,
      claim: null,
      // array of Steps this step depends on
      dependsOn: [],
      // array of API validation warnings
      warnings: null,
    };
  }

  get fields() {
    return this.stepDefinition.fields;
  }

  get name() {
    return this.stepDefinition.name;
  }

  // page user is navigated to when clicking into step
  get href() {
    return this.stepDefinition.initialPage;
  }

  get status() {
    if (this.isDisabled) {
      return "disabled";
    }

    if (this.isComplete) {
      return "completed";
    }

    if (this.isInProgress) {
      return "in_progress";
    }

    return "not_started";
  }

  get isComplete() {
    // TODO remove once api returns validations
    if (!this.warnings) return true;

    return !this.warnings.some((warning) =>
      this.fields.includes(warning.field)
    );
  }

  get isInProgress() {
    return this.fields.some((field) => fieldHasValue(field, this.claim));
  }

  get isDisabled() {
    if (!this.dependsOn.length) return false;

    return this.stepDefinition.dependsOn.some(
      (dependedOnStep) => !dependedOnStep.isComplete
    );
  }
}
