import { get, groupBy, isEmpty, map } from "lodash";
import getRelevantIssues from "../utils/getRelevantIssues";

type Context = Record<string, unknown>;

/**
 * Unique identifiers for steps in the portal application. The values
 * map to events in our routing state machine.
 * @enum {string}
 */
export const ClaimSteps = {
  verifyId: "VERIFY_ID",
  employerInformation: "EMPLOYER_INFORMATION",
  leaveDetails: "LEAVE_DETAILS",
  otherLeave: "OTHER_LEAVE",
  reviewAndConfirm: "REVIEW_AND_CONFIRM",
  payment: "PAYMENT",
  uploadCertification: "UPLOAD_CERTIFICATION",
  uploadId: "UPLOAD_ID",
} as const;

const fieldHasValue = (fieldPath: string, context: Context) => {
  const value = get(context, fieldPath);

  if (typeof value === "boolean") return true;

  if (typeof value === "number") return true;

  return !isEmpty(value);
};

/**
 * A model that represents a section in a user flow
 * and gives the completion status based on the current
 * state of user data
 * @returns {Step}
 */
export default class Step {
  name: string;
  /**
   * Optional method for evaluating whether a step is not applicable,
   * based on the Step's `context`. This is useful if a Step
   * may be skipped for certain types of applications
   */
  notApplicableCond?: (context: Context) => boolean;
  /**
   * What StepGroup number is it associated with (e.g Part 2)
   */
  group: number;
  /**
   * object representing all pages in this step keyed by the page route
   * @see ../flows
   */
  pages: Array<{
    route: string;
    meta: { step: string; fields: string[]; applicableRules: string[] };
  }>;

  /**
   * Array of steps that must be completed before this step
   */
  dependsOn?: Step[] = [];
  /**
   * Optional method for evaluating whether a step is complete,
   * based on the Step's `context`. This is useful if a Step
   * has no form fields associated with it.
   */
  completeCond?: (context: Context) => boolean;
  /**
   * Allow/Disallow entry into this step to edit answers to its questions
   */
  editable? = true;
  /**
   * Context used for evaluating a step's status
   */
  context?: Context;
  /**
   * Array of validation warnings from the API, used for determining
   * the completion status of Steps that include fields. You can exclude
   * this if a Step doesn't include a field, or if it has its own
   * completeCond set.
   */
  warnings?: Array<Record<string, unknown>>;

  constructor(
    attrs: Omit<
      Step,
      | "fields"
      | "isComplete"
      | "isDisabled"
      | "isInProgress"
      | "isNotApplicable"
      | "status"
    >
  ) {
    Object.assign(this, attrs);
  }

  get fields() {
    return this.pages.flatMap((page) => page.meta.fields);
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

    const issues = getRelevantIssues([], this.warnings || [], this.pages);

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
   * @param {BenefitsApplication} [context.claim]
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

    const verifyId = new Step({
      name: ClaimSteps.verifyId,
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'isSubmitted' does not exist on type '{}'... Remove this comment to see the full error message
      editable: !claim.isSubmitted,
      group: 1,
      pages: pagesByStep[ClaimSteps.verifyId],
      context,
      warnings,
    });

    const employerInformation = new Step({
      name: ClaimSteps.employerInformation,
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'isSubmitted' does not exist on type '{}'... Remove this comment to see the full error message
      editable: !claim.isSubmitted,
      group: 1,
      pages: pagesByStep[ClaimSteps.employerInformation],
      dependsOn: [verifyId],
      context,
      warnings,
    });

    const leaveDetails = new Step({
      name: ClaimSteps.leaveDetails,
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'isSubmitted' does not exist on type '{}'... Remove this comment to see the full error message
      editable: !claim.isSubmitted,
      group: 1,
      pages: pagesByStep[ClaimSteps.leaveDetails],
      dependsOn: [verifyId, employerInformation],
      context,
      warnings,
    });

    const otherLeave = new Step({
      name: ClaimSteps.otherLeave,
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'isSubmitted' does not exist on type '{}'... Remove this comment to see the full error message
      editable: !claim.isSubmitted,
      group: 1,
      pages: pagesByStep[ClaimSteps.otherLeave],
      dependsOn: [verifyId, leaveDetails, employerInformation],
      context,
      warnings,
    });

    const reviewAndConfirm = new Step({
      name: ClaimSteps.reviewAndConfirm,
      completeCond: (context) => get(context.claim, "isSubmitted"),
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'isSubmitted' does not exist on type '{}'... Remove this comment to see the full error message
      editable: !claim.isSubmitted,
      group: 1,
      pages: pagesByStep[ClaimSteps.reviewAndConfirm],
      dependsOn: [verifyId, employerInformation, leaveDetails, otherLeave],
      context,
    });

    const payment = new Step({
      name: ClaimSteps.payment,
      completeCond: (context) =>
        get(context.claim, "has_submitted_payment_preference"),
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'has_submitted_payment_preference' does n... Remove this comment to see the full error message
      editable: !claim.has_submitted_payment_preference,
      group: 2,
      pages: pagesByStep[ClaimSteps.payment],
      dependsOn: [
        verifyId,
        employerInformation,
        leaveDetails,
        otherLeave,
        reviewAndConfirm,
      ],
      context,
      warnings,
    });

    const uploadId = new Step({
      completeCond: (context) => {
        return (
          Array.isArray(context.idDocuments) && !!context.idDocuments.length
        );
      },
      name: ClaimSteps.uploadId,
      group: 3,
      pages: pagesByStep[ClaimSteps.uploadId],
      dependsOn: [
        verifyId,
        employerInformation,
        leaveDetails,
        otherLeave,
        reviewAndConfirm,
        payment,
      ],
      context,
    });

    const uploadCertification = new Step({
      completeCond: (context) => {
        return (
          Array.isArray(context.certificationDocuments) &&
          !!context.certificationDocuments.length
        );
      },
      name: ClaimSteps.uploadCertification,
      notApplicableCond: (context) =>
        get(context.claim, "leave_details.has_future_child_date") === true,
      group: 3,
      pages: pagesByStep[ClaimSteps.uploadCertification],
      dependsOn: [
        verifyId,
        employerInformation,
        leaveDetails,
        otherLeave,
        reviewAndConfirm,
        payment,
      ],
      context,
    });

    return [
      verifyId,
      employerInformation,
      leaveDetails,
      otherLeave,
      reviewAndConfirm,
      payment,
      uploadId,
      uploadCertification,
    ];
  };
}
