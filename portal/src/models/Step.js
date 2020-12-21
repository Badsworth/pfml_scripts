import { get, groupBy, isEmpty, map } from "lodash";
import BaseModel from "./BaseModel";
import { createRouteWithQuery } from "../utils/routeWithParams";
import getRelevantIssues from "../utils/getRelevantIssues";
import routes from "../routes";

/**
 * Unique identifiers for steps in the portal application
 * @enum {string}
 */
export const ClaimSteps = {
  verifyId: "verifyId",
  employerInformation: "employerInformation",
  leaveDetails: "leaveDetails",
  otherLeave: "otherLeave",
  reviewAndConfirm: "reviewAndConfirm",
  payment: "payment",
  uploadId: "uploadId",
  uploadCertification: "uploadCertification",
};

const fieldHasValue = (fieldPath, context) => {
  const value = get(context, fieldPath);

  if (typeof value === "boolean") return true;

  if (typeof value === "number") return true;

  if (value instanceof BaseModel) return !value.isDefault();

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
       * @type {Function}
       * Optional method for evaluating whether a step is not applicable,
       * based on the Step's `context`. This is useful if a Step
       * may be skipped for certain types of applications
       */
      notApplicableCond: null,
      /**
       * @type {number}
       * If this belongs within a StepGroup, what StepGroup number is it associated with (e.g Part 2)
       */
      group: null,
      /**
       * @type {Array<{ route: string, meta: { step: string, fields: string[], applicableRules: string[] }}>}
       * object representing all pages in this step keyed by the page route
       * @see ../flows
       */
      pages: null,
      /**
       * @type {string}
       * Optionally define which route a user should be directed to for this Step.
       * By default, the first entry in `pages` will be used.
       */
      initialPageRoute: null,
      /**
       * @type {Step[]}
       * Array of steps that must be completed before this step
       */
      dependsOn: [],
      /**
       * @type {Function}
       * Optional method for evaluating whether a step is complete,
       * based on the Step's `context`. This is useful if a Step
       * has no form fields associated with it.
       */
      completeCond: null,
      /**
       * @type {boolean}
       * Allow/Disallow entry into this step to edit answers to its questions
       */
      editable: true,
      /**
       * @type {object}
       * Context used for evaluating a step's status
       */
      context: null,
      /**
       * @type {object[]}
       * Array of validation warnings from the API, used for determining
       * the completion status of Steps that include fields. You can exclude
       * this if a Step doesn't include a field, or if it has its own
       * completeCond set.
       */
      warnings: null,
    };
  }

  get fields() {
    return this.pages.flatMap((page) => page.meta.fields);
  }

  get initialPage() {
    if (this.initialPageRoute) return this.initialPageRoute;
    return this.pages[0].route;
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

    if (this.isNotApplicable) {
      return "not_applicable";
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
    if (this.completeCond) return this.completeCond(this.context);
    // TODO (CP-625): remove once api returns validations
    // <WorkAround>
    if (!this.warnings) {
      return this.fields.every((field) => {
        // Ignore optional and conditional questions for now,
        // so that we can show a "Completed" checklist.
        // Fields names can be partial, to ignore an array or object of fields.
        const ignoredField = [
          // TODO (CP-567): Remove reduction fields once the Reductions step utilizes the warnings
          "claim.employer_benefits",
          "claim.other_incomes",
          "claim.previous_leaves",
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

    const issues = getRelevantIssues([], this.warnings, this.pages);

    if (process.env.NODE_ENV === "development" && issues.length) {
      // eslint-disable-next-line no-console
      console.log(`${this.name} has warnings`, issues);
    }

    return issues.length === 0;
  }

  get isInProgress() {
    return this.fields.some((field) => fieldHasValue(field, this.context));
  }

  get isNotApplicable() {
    if (this.notApplicableCond) return this.notApplicableCond(this.context);

    return false;
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
   * @param {Claim} [context.claim]
   * @param {Document[]} [context.certificationDocuments]
   * @param {Document[]} [context.idDocuments]
   * @param {object[]} [warnings] - array of validation warnings returned from API
   * @returns {Step[]}
   * @example createClaimStepsFromMachine(claimFlowConfig, { claim: { first_name: "Bud" } })
   */
  static createClaimStepsFromMachine = (
    machineConfigs,
    context = {
      claim: {},
      certificationDocuments: [],
      idDocuments: [],
    },
    warnings
  ) => {
    const { claim } = context;
    const pages = map(machineConfigs.states, (state, key) =>
      Object.assign({ route: key, meta: state.meta })
    );
    const pagesByStep = groupBy(pages, "meta.step");

    // TODO (CP-1346) Remove this filter logic once the claimantShowOtherLeaveStep feature flag is no longer relevant
    const filterOutHiddenSteps = (steps) => {
      if (context.showOtherLeaveStep) {
        return steps;
      } else {
        return steps.filter((step) => step.name !== ClaimSteps.otherLeave);
      }
    };

    const verifyId = new Step({
      name: ClaimSteps.verifyId,
      editable: !claim.isSubmitted,
      group: 1,
      pages: pagesByStep[ClaimSteps.verifyId],
      context,
      warnings,
    });

    const employerInformation = new Step({
      name: ClaimSteps.employerInformation,
      editable: !claim.isSubmitted,
      group: 1,
      pages: pagesByStep[ClaimSteps.employerInformation],
      dependsOn: [verifyId],
      context,
      warnings,
    });

    const leaveDetails = new Step({
      name: ClaimSteps.leaveDetails,
      editable: !claim.isSubmitted,
      group: 1,
      pages: pagesByStep[ClaimSteps.leaveDetails],
      dependsOn: [verifyId, employerInformation],
      context,
      warnings,
    });

    const otherLeave = new Step({
      name: ClaimSteps.otherLeave,
      editable: !claim.isSubmitted,
      group: 1,
      pages: pagesByStep[ClaimSteps.otherLeave],
      dependsOn: [verifyId, leaveDetails, employerInformation],
      context,
      // TODO (CP-567): Pass in warnings when at least one of this step's required fields are
      // integrated with the API and has a validation rule
      // warnings,
    });

    const reviewAndConfirm = new Step({
      name: ClaimSteps.reviewAndConfirm,
      completeCond: (context) => context.claim.isSubmitted,
      editable: !claim.isSubmitted,
      group: 1,
      pages: pagesByStep[ClaimSteps.reviewAndConfirm],
      // TODO (CP-1272): Utilize the Checklist state node's transitions instead of
      // relying on the array order or the extra `initialPageRoute` property
      initialPageRoute: claim.isBondingLeave
        ? routes.applications.bondingLeaveAttestation
        : routes.applications.review,
      dependsOn: filterOutHiddenSteps([
        verifyId,
        employerInformation,
        leaveDetails,
        otherLeave,
      ]),
      context,
    });

    const payment = new Step({
      name: ClaimSteps.payment,
      completeCond: (context) => context.claim.has_submitted_payment_preference,
      editable: !claim.has_submitted_payment_preference,
      group: 2,
      pages: pagesByStep[ClaimSteps.payment],
      dependsOn: filterOutHiddenSteps([
        verifyId,
        employerInformation,
        leaveDetails,
        otherLeave,
        reviewAndConfirm,
      ]),
      context,
      warnings,
    });

    const uploadId = new Step({
      completeCond: (context) => !!context.idDocuments.length,
      name: ClaimSteps.uploadId,
      group: 3,
      pages: pagesByStep[ClaimSteps.uploadId],
      dependsOn: filterOutHiddenSteps([
        verifyId,
        employerInformation,
        leaveDetails,
        otherLeave,
        reviewAndConfirm,
        payment,
      ]),
      context,
    });

    const uploadCertification = new Step({
      completeCond: (context) => !!context.certificationDocuments.length,
      name: ClaimSteps.uploadCertification,
      notApplicableCond: (context) =>
        get(context.claim, "leave_details.has_future_child_date") === true,
      group: 3,
      pages: pagesByStep[ClaimSteps.uploadCertification],
      dependsOn: filterOutHiddenSteps([
        verifyId,
        employerInformation,
        leaveDetails,
        otherLeave,
        reviewAndConfirm,
        payment,
      ]),
      context,
    });

    return filterOutHiddenSteps([
      verifyId,
      employerInformation,
      leaveDetails,
      otherLeave,
      reviewAndConfirm,
      payment,
      uploadId,
      uploadCertification,
    ]);
  };
}
