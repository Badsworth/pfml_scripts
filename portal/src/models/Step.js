import { get, groupBy, map } from "lodash";
import BaseModel from "./BaseModel";
import { createRouteWithQuery } from "../utils/routeWithParams";

/**
 * Unique identifiers for steps in the portal application
 * @enum {string}
 */
export const ClaimSteps = {
  verifyId: "verifyId",
  leaveDetails: "leaveDetails",
  employerInformation: "employerInformation",
  otherLeave: "otherLeave",
  payment: "payment",
};

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
      /**
       * @type {string}
       */
      name: null,
      /**
       * @type {object[]}
       * { route: "page/route", step: "verifyId", fields: ["first_name"] }
       * object representing all pages in this step keyed by the page route
       * @see ../routes/claim-flow-configs
       */
      pages: null,
      /**
       * @type {Step[]}
       * Array of steps that must be completed before this step
       */
      dependsOn: [],
      /**
       * @type {Claim}
       */
      claim: null,
      /**
       * @type {object[]}
       * Array of validation warnings and errors from the API
       */
      warnings: null,
    };
  }

  // TODO remove when all steps are populated with pages
  get _pages() {
    return this.pages || [];
  }

  get fields() {
    return this._pages.flatMap((page) => page.fields);
  }

  get initialPage() {
    // TODO remove when all steps are populated with pages
    return (this._pages[0] || {}).route || "#";
  }

  // page user is navigated to when clicking into step
  get href() {
    return createRouteWithQuery(this.initialPage, {
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
   * Create an array of Steps from routing machine configuration
   * @see ../routes/claim-flow-configs
   * @param {object} machineConfigs - configuration object for routing machine
   * @param {Claim} claim - a claim
   * @param {Array} warnings - array of validation warnings returned from API
   * @returns {Step[]}
   */
  static createClaimStepsFromMachine = (machineConfigs, claim, warnings) => {
    const pages = map(machineConfigs.states, (state, key) =>
      Object.assign({ route: key }, state.meta)
    );
    const pagesByStep = groupBy(pages, "step");

    const verifyId = new Step({
      name: ClaimSteps.verifyId,
      pages: pagesByStep[ClaimSteps.verifyId],
      claim,
      warnings,
    });

    const leaveDetails = new Step({
      name: ClaimSteps.leaveDetails,
      pages: pagesByStep[ClaimSteps.leaveDetails],
      dependsOn: [verifyId],
      claim,
      warnings,
    });

    const employerInformation = new Step({
      name: ClaimSteps.employerInformation,
      pages: pagesByStep[ClaimSteps.employerInformation],
      dependsOn: [verifyId, leaveDetails],
      claim,
      warnings,
    });

    const otherLeave = new Step({
      name: ClaimSteps.otherLeave,
      pages: pagesByStep[ClaimSteps.otherLeave],
      dependsOn: [verifyId, leaveDetails],
      claim,
      warnings,
    });

    const payment = new Step({
      name: ClaimSteps.payment,
      pages: pagesByStep[ClaimSteps.payment],
      dependsOn: [verifyId, leaveDetails],
      claim,
      warnings,
    });

    return [verifyId, leaveDetails, employerInformation, otherLeave, payment];
  };
}
