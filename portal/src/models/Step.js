import { get, groupBy, isEmpty, map } from "lodash";
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

const fieldHasValue = (fieldPath, context) => {
  const value = get(context, fieldPath);

  if (typeof value === "boolean") return true;

  return !isEmpty(value);
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
       * @see ../flows
       */
      pages: null,
      /**
       * @type {Step[]}
       * Array of steps that must be completed before this step
       */
      dependsOn: [],
      /**
       * @type {object}
       * Context used for evaluating a step's status
       */
      context: null,
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
      claim_id: get(this.context, "claim.application_id"),
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
    // TODO (CP-625): remove once api returns validations
    // <WorkAround>
    if (!this.warnings) {
      return this.fields.every((field) => {
        // Ignore optional and conditional questions for now,
        // so that we can show a "Completed" checklist.
        // Fields names can be partial, to ignore an array or object of fields.
        const ignoredField = [
          "claim.employer_benefits",
          "claim.leave_details.intermittent_leave_periods[0]",
          "claim.middle_name",
          "claim.other_incomes",
          "claim.pregnant_or_recent_birth",
          "claim.previous_leaves",
          "claim.temp.leave_details.avg_weekly_work_hours",
          "claim.temp.leave_details.continuous_leave_periods[0]",
          "claim.temp.leave_details.bonding.date_of_child",
          "claim.temp.leave_details.end_date",
          "claim.temp.leave_details.start_date",
          "claim.temp.leave_details.reduced_schedule_leave_periods[0]",
          "claim.temp.payment_preferences[0].account_details",
          "claim.temp.payment_preferences[0].destination_address",
        ].some((ignoredFieldName) => field.includes(ignoredFieldName));

        const hasValue = fieldHasValue(field, this.context);

        if (
          process.env.NODE_ENV === "development" &&
          !hasValue &&
          !ignoredField
        ) {
          // eslint-disable-next-line no-console
          console.log(
            `${field} missing value, received`,
            get(this.context, field)
          );
        }

        return hasValue || ignoredField;
      });
    }
    // </WorkAround>

    return !this.warnings.some((warning) =>
      this.fields.includes(warning.field)
    );
  }

  get isInProgress() {
    return this.fields.some((field) => fieldHasValue(field, this.context));
  }

  get isDisabled() {
    if (!this.dependsOn.length) return false;

    return this.dependsOn.some((dependedOnStep) => !dependedOnStep.isComplete);
  }

  /**
   * Create an array of Steps from routing machine configuration
   * @see ../flows/index.js
   * @param {object} machineConfigs - configuration object for routing machine
   * @param {object} context - used for evaluating a step's status
   * @param {object[]} [warnings] - array of validation warnings returned from API
   * @returns {Step[]}
   * @example createClaimStepsFromMachine(claimFlowConfig, { claim: { first_name: "Bud" } })
   */
  static createClaimStepsFromMachine = (machineConfigs, context, warnings) => {
    const pages = map(machineConfigs.states, (state, key) =>
      Object.assign({ route: key }, state.meta)
    );
    const pagesByStep = groupBy(pages, "step");
    const verifyId = new Step({
      name: ClaimSteps.verifyId,
      pages: pagesByStep[ClaimSteps.verifyId],
      context,
      warnings,
    });

    const leaveDetails = new Step({
      name: ClaimSteps.leaveDetails,
      pages: pagesByStep[ClaimSteps.leaveDetails],
      dependsOn: [verifyId],
      context,
      warnings,
    });

    const employerInformation = new Step({
      name: ClaimSteps.employerInformation,
      pages: pagesByStep[ClaimSteps.employerInformation],
      dependsOn: [verifyId, leaveDetails],
      context,
      warnings,
    });

    const otherLeave = new Step({
      name: ClaimSteps.otherLeave,
      pages: pagesByStep[ClaimSteps.otherLeave],
      dependsOn: [verifyId, leaveDetails],
      context,
      warnings,
    });

    const payment = new Step({
      name: ClaimSteps.payment,
      pages: pagesByStep[ClaimSteps.payment],
      dependsOn: [verifyId, leaveDetails],
      context,
      warnings,
    });

    return [verifyId, leaveDetails, employerInformation, otherLeave, payment];
  };
}
