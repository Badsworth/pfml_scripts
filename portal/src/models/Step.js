import BaseModel from "./BaseModel";
import { createRouteWithQuery } from "../utils/routeWithParams";
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
    return createRouteWithQuery(this.stepDefinition.initialPage, {
      claim_id: this.claim.application_id,
    });
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

    return this.dependsOn.some((dependedOnStep) => !dependedOnStep.isComplete);
  }

  /**
   * Create an array of Steps from their definitions
   * @param {StepDefinition[]} stepDefinitions - array of stepDefinitions in the correct order
   * @param {Claim} claim - a claim
   * @param {Array} warnings - array of validation warnings returned from API
   * @returns {Step[]}
   */
  static createStepsFromDefinitions = (stepDefinitions, claim, warnings) => {
    // Store newly created steps in memory so they can
    // be referenced in subsequent steps' `dependsOn` property
    const stepMap = stepDefinitions.reduce((result, stepDefinition) => {
      result[stepDefinition.name] = new Step({
        stepDefinition,
        claim,
        warnings,
        dependsOn: stepDefinition.dependsOn.map((dependedOn) => {
          const dependedOnStep = result[dependedOn.name];
          if (!dependedOnStep)
            throw new Error(
              `Could not find ${dependedOn.name} step in provided StepDefinitions. Make sure it is defined before ${stepDefinition.name} in your array.`
            );
          return dependedOnStep;
        }),
      });

      return result;
    }, {});

    return Object.values(stepMap);
  };
}
