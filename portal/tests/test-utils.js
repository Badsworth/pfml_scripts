import {
  BankAccountType,
  PaymentPreferenceMethod,
} from "../src/models/PaymentPreference";
import Claim, {
  ClaimStatus,
  ContinuousLeavePeriod,
  DurationBasis,
  EmploymentStatus,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
  PhoneType,
  ReasonQualifier,
  ReducedScheduleLeavePeriod,
  WorkPattern,
  WorkPatternDay,
  WorkPatternType,
} from "../src/models/Claim";
import Document, { DocumentType } from "../src/models/Document";
import EmployerBenefit, {
  EmployerBenefitType,
  IncomeFrequency,
} from "../src/models/EmployerBenefit";
import OtherIncome, { OtherIncomeType } from "../src/models/OtherIncome";
import PreviousLeave, {
  PreviousLeaveReason,
} from "../src/models/PreviousLeave";
import { mount, shallow } from "enzyme";
import Address from "../src/models/Address";
import AppErrorInfo from "../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../src/models/AppErrorInfoCollection";
import ClaimCollection from "../src/models/ClaimCollection";
import EmployerClaim from "../src/models/EmployerClaim";
import LeaveReason from "../src/models/LeaveReason";
import React from "react";
import User from "../src/models/User";
import { act } from "react-dom/test-utils";
import merge from "lodash/merge";
import set from "lodash/set";
import times from "lodash/times";
import useAppLogic from "../src/hooks/useAppLogic";

export class BaseMockClaimBuilder {
  employed() {
    set(this.claimAttrs, "employer_fein", "12-3456789");
    set(this.claimAttrs, "leave_details.employer_notified", true);
    set(this.claimAttrs, "hours_worked_per_week", 30);
    set(
      this.claimAttrs,
      "leave_details.employer_notification_date",
      "2021-01-01"
    );
    return this;
  }

  /**
   * @returns {BaseMockClaimBuilder}
   */
  absenceId() {
    set(this.claimAttrs, "fineos_absence_id", "NTN-111-ABS-01");
    return this;
  }

  address(attrs) {
    set(
      this.claimAttrs,
      "residential_address",
      attrs
        ? new Address(attrs)
        : new Address({
            city: "Boston",
            line_1: "1234 My St.",
            line_2: null,
            state: "MA",
            zip: "00000",
          })
    );
    return this;
  }

  continuous(leavePeriodAttrs = {}) {
    set(
      this.claimAttrs,
      "leave_details.continuous_leave_periods[0]",
      new ContinuousLeavePeriod(
        Object.assign(
          {
            leave_period_id: "mock-leave-period-id",
            start_date: "2021-01-01",
            end_date: "2021-06-01",
          },
          leavePeriodAttrs
        )
      )
    );
    return this;
  }

  intermittent(leavePeriodAttrs = {}) {
    set(
      this.claimAttrs,
      "leave_details.intermittent_leave_periods[0]",
      new IntermittentLeavePeriod(
        Object.assign(
          {
            leave_period_id: "mock-leave-period-id",
            start_date: "2021-02-01",
            end_date: "2021-07-01",
            duration: 3,
            duration_basis: DurationBasis.hours,
            frequency: 6,
            frequency_interval: 6,
            frequency_interval_basis: FrequencyIntervalBasis.months,
          },
          leavePeriodAttrs
        )
      )
    );
    return this;
  }

  reducedSchedule(leavePeriodAttrs = {}) {
    set(
      this.claimAttrs,
      "leave_details.reduced_schedule_leave_periods[0]",
      new ReducedScheduleLeavePeriod(
        Object.assign(
          {
            leave_period_id: "mock-leave-period-id",
            start_date: "2021-02-01",
            end_date: "2021-07-01",
          },
          leavePeriodAttrs
        )
      )
    );
    return this;
  }

  bondingLeaveReason() {
    set(this.claimAttrs, "leave_details.reason", LeaveReason.bonding);
    return this;
  }

  medicalLeaveReason() {
    set(this.claimAttrs, "leave_details.reason", LeaveReason.medical);
    return this;
  }

  otherIncome() {
    set(this.claimAttrs, "other_incomes", [
      new OtherIncome({
        income_amount_dollars: 125,
        income_end_date: "2021-01-01",
        income_start_date: "2021-01-30",
        income_type: OtherIncomeType.otherEmployer,
      }),
    ]);
    set(this.claimAttrs, "temp.has_other_incomes", true);
    set(this.claimAttrs, "other_incomes_awaiting_approval", false);
    return this;
  }

  previousLeavePregnancyFromOtherEmployer() {
    set(this.claimAttrs, "previous_leaves", [
      new PreviousLeave({
        id: 1,
        is_for_current_employer: false,
        leave_end_date: "2020-02-01",
        leave_reason: PreviousLeaveReason.pregnancy,
        leave_start_date: "2020-01-01",
      }),
    ]);
    return this;
  }

  previousLeaveMedicalFromCurrentEmployer() {
    set(this.claimAttrs, "previous_leaves", [
      new PreviousLeave({
        id: 1,
        is_for_current_employer: true,
        leave_end_date: "2020-02-01",
        leave_reason: PreviousLeaveReason.medical,
        leave_start_date: "2020-01-01",
      }),
    ]);
    return this;
  }

  employerBenefit(attrs) {
    set(
      this.claimAttrs,
      "employer_benefits",
      attrs
        ? attrs.map((attr) => new EmployerBenefit(attr))
        : [
            new EmployerBenefit({
              benefit_amount_dollars: 500,
              benefit_amount_frequency: IncomeFrequency.weekly,
              benefit_end_date: "2021-02-01",
              benefit_start_date: "2021-01-01",
              benefit_type: EmployerBenefitType.familyOrMedicalLeave,
              id: 1,
            }),
          ]
    );
    return this;
  }
}

/**
 * @class Employer Claim
 * @example
 *  new MockEmployerClaimBuilder()
 *    .completed()
 *    .create();
 */
export class MockEmployerClaimBuilder extends BaseMockClaimBuilder {
  constructor(middleName = "") {
    super();
    this.claimAttrs = {
      first_name: "Jane",
      middle_name: middleName,
      last_name: "Doe",
      date_of_birth: "****-07-17",
      tax_identifier: "***-**-1234",
      follow_up_date: "2020-10-10",
    };
  }

  /**
   * @returns {MockEmployerClaimBuilder}
   */
  completed() {
    this.employed();
    this.address();
    this.continuous();
    this.reducedSchedule();
    this.previousLeavePregnancyFromOtherEmployer();
    this.employerBenefit();
    this.absenceId();
    set(this.claimAttrs, "leave_details.reason", LeaveReason.medical);
    return this;
  }

  /**
   * @returns {EmployerClaim}
   */
  create() {
    return new EmployerClaim(this.claimAttrs);
  }
}

/**
 * A class that has chainable functions for conveniently creating mock claims
 * with prefilled data. Chain together multiple function calls, then call
 * the `create` function at the end to get the Claim object.
 * @class
 * @example
 *  new MockClaimBuilder()
 *    .continuous()
 *    .intermittent()
 *    .create();
 */
export class MockClaimBuilder extends BaseMockClaimBuilder {
  constructor() {
    super();
    this.claimAttrs = {
      application_id: "mock_application_id",
      status: ClaimStatus.started,
    };
  }

  /**
   * @returns {MockClaimBuilder}
   */
  id(application_id) {
    set(this.claimAttrs, "application_id", application_id);
    return this;
  }

  /**
   * @param {object} [leavePeriodAttrs]
   * @returns {MockClaimBuilder}
   */
  continuous(leavePeriodAttrs = {}) {
    set(this.claimAttrs, "has_continuous_leave_periods", true);
    super.continuous(leavePeriodAttrs);
    return this;
  }

  /**
   * Sets payment method to paper check
   * @returns {MockClaimBuilder}
   */
  check() {
    set(
      this.claimAttrs,
      "payment_preference.payment_method",
      PaymentPreferenceMethod.check
    );
    return this;
  }

  /**
   * Sets payment method to direct deposit
   * @returns {MockClaimBuilder}
   */
  directDeposit() {
    set(
      this.claimAttrs,
      "payment_preference.payment_method",
      PaymentPreferenceMethod.ach
    );
    set(this.claimAttrs, "payment_preference.account_number", "091000022");
    set(
      this.claimAttrs,
      "payment_preference.bank_account_type",
      BankAccountType.checking
    );
    set(this.claimAttrs, "payment_preference.routing_number", "1234567890");
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  hasOtherId() {
    set(this.claimAttrs, "has_state_id", false);
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  hasStateId() {
    set(this.claimAttrs, "has_state_id", true);
    set(this.claimAttrs, "mass_id", "*********");
    return this;
  }

  /**
   * @param {object} [leavePeriodAttrs]
   * @returns {MockClaimBuilder}
   */
  intermittent(leavePeriodAttrs = {}) {
    set(this.claimAttrs, "has_intermittent_leave_periods", true);
    super.intermittent(leavePeriodAttrs);
    return this;
  }

  /**
   * @param {object} [leavePeriodAttrs]
   * @returns {MockClaimBuilder}
   */
  reducedSchedule(leavePeriodAttrs = {}) {
    set(this.claimAttrs, "has_reduced_schedule_leave_periods", true);
    super.reducedSchedule({
      monday_off_minutes: 6.5 * 60,
      friday_off_minutes: 8 * 60,
      ...leavePeriodAttrs,
    });
    return this;
  }

  /**
   * @param {string} birthDate Child's birth date in ISO-8601 format. Defaults
   * to "2012-02-12"
   * @returns {MockClaimBuilder}
   */
  bondingBirthLeaveReason(birthDate = "2012-02-12") {
    this.bondingLeaveReason();
    set(
      this.claimAttrs,
      "leave_details.reason_qualifier",
      ReasonQualifier.newBorn
    );
    set(this.claimAttrs, "leave_details.child_birth_date", birthDate);
    return this;
  }

  /**
   * @param {string} placementDate Child's placement date in ISO-8601 format. Defaults
   * to "2020-02-14"
   * @returns {MockClaimBuilder}
   */
  bondingAdoptionLeaveReason(placementDate = "2012-02-14") {
    this.bondingLeaveReason();
    set(
      this.claimAttrs,
      "leave_details.reason_qualifier",
      ReasonQualifier.adoption
    );
    set(this.claimAttrs, "leave_details.child_placement_date", placementDate);
    return this;
  }

  /**
   * @param {string} placementDate Child's placement date in ISO-8601 format. Defaults
   * to "2020-02-14"
   * @returns {MockClaimBuilder}
   */
  bondingFosterCareLeaveReason(placementDate = "2012-02-14") {
    this.bondingLeaveReason();
    set(
      this.claimAttrs,
      "leave_details.reason_qualifier",
      ReasonQualifier.fosterCare
    );
    set(this.claimAttrs, "leave_details.child_placement_date", placementDate);
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  hasFutureChild() {
    this.bondingLeaveReason();
    set(this.claimAttrs, "leave_details.has_future_child_date", true);
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  employed() {
    set(this.claimAttrs, "employment_status", EmploymentStatus.employed);
    super.employed();
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  noOtherLeave() {
    set(this.claimAttrs, "temp.has_employer_benefits", false);
    set(this.claimAttrs, "temp.has_other_incomes", false);
    set(this.claimAttrs, "temp.has_previous_leaves", false);
    return this;
  }

  noPreviousLeave() {
    set(this.claimAttrs, "temp.has_previous_leaves", false);
    return this;
  }

  previousLeavePregnancyFromOtherEmployer() {
    super.previousLeavePregnancyFromOtherEmployer();
    set(this.claimAttrs, "temp.has_previous_leaves", true);
    return this;
  }

  previousLeaveMedicalFromCurrentEmployer() {
    super.previousLeaveMedicalFromCurrentEmployer();
    set(this.claimAttrs, "temp.has_previous_leaves", true);
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  notifiedEmployer() {
    set(this.claimAttrs, "leave_details.employer_notified", true);
    set(
      this.claimAttrs,
      "leave_details.employer_notification_date",
      "2020-08-26"
    );
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  notNotifiedEmployer() {
    set(this.claimAttrs, "leave_details.employer_notified", false);
    set(this.claimAttrs, "leave_details.employer_notification_date", null);
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  pregnant() {
    set(this.claimAttrs, "leave_details.pregnant_or_recent_birth", true);
    return this;
  }

  /**
   * All required data is present but the claim hasn't been marked
   * as Completed yet in the API
   * @returns {MockClaimBuilder}
   */
  complete() {
    this.submitted();
    this.paymentPrefSubmitted();
    return this;
  }

  /**
   * Claim has all required data and has been marked as completed in the API
   * @returns {MockClaimBuilder}
   */
  completed() {
    this.complete();
    set(this.claimAttrs, "status", ClaimStatus.completed);

    return this;
  }

  /**
   * Part 1 steps are complete but not yet submitted to API
   * @param {object} [options]
   * @param {boolean} [options.excludeLeavePeriod]
   * @returns {MockClaimBuilder}
   */
  part1Complete(options = {}) {
    this.verifiedId();
    this.medicalLeaveReason();
    this.employed();
    this.noOtherLeave();
    this.address();
    this.workPattern({ work_pattern_type: WorkPatternType.fixed });

    if (!options.excludeLeavePeriod) this.continuous();

    return this;
  }

  /**
   * Part 1 steps are complete and submitted to API
   * @returns {MockClaimBuilder}
   */
  submitted() {
    this.part1Complete();
    this.absenceId();
    set(this.claimAttrs, "status", ClaimStatus.submitted);

    return this;
  }

  /**
   * Part 2 step is completed and submitted to API
   * @returns {MockClaimBuilder}
   */
  paymentPrefSubmitted() {
    this.submitted();
    this.directDeposit();
    set(this.claimAttrs, "has_submitted_payment_preference", true);

    return this;
  }

  /**
   * @param {object} attrs Address object
   * @returns {MockClaimBuilder}
   */
  address(attrs) {
    set(this.claimAttrs, "has_mailing_address", false);
    super.address(attrs);
    return this;
  }

  /**
   * @param {object} attrs Address object
   * @returns {MockClaimBuilder}
   */
  mailingAddress(attrs) {
    set(this.claimAttrs, "has_mailing_address", true);
    set(
      this.claimAttrs,
      "mailing_address",
      attrs
        ? new Address(attrs)
        : new Address({
            city: "Boston",
            line_1: "124 My St.",
            line_2: null,
            state: "MA",
            zip: "00000",
          })
    );
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  verifiedId(middleName) {
    set(this.claimAttrs, "first_name", "Jane");
    set(this.claimAttrs, "middle_name", middleName || "");
    set(this.claimAttrs, "last_name", "Doe");
    set(this.claimAttrs, "phone", {
      phone_number: "123-456-****",
      phone_type: PhoneType.cell,
    });
    set(this.claimAttrs, "date_of_birth", "****-07-17");
    set(this.claimAttrs, "tax_identifier", "***-**-****");
    this.address();
    this.hasStateId();
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  workPattern(attrs = {}) {
    set(this.claimAttrs, "work_pattern", new WorkPattern(attrs));

    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  fixedWorkPattern() {
    set(
      this.claimAttrs,
      "work_pattern",
      new WorkPattern({
        work_pattern_type: WorkPatternType.fixed,
        work_pattern_days: [
          new WorkPatternDay({
            day_of_week: "Sunday",
            week_number: 1,
            minutes: 0,
          }),
          new WorkPatternDay({
            day_of_week: "Monday",
            week_number: 1,
            minutes: 8 * 60,
          }),
          new WorkPatternDay({
            day_of_week: "Tuesday",
            week_number: 1,
            minutes: 8 * 60,
          }),
          new WorkPatternDay({
            day_of_week: "Wednesday",
            week_number: 1,
            minutes: 8 * 60,
          }),
          new WorkPatternDay({
            day_of_week: "Thursday",
            week_number: 1,
            minutes: 8 * 60,
          }),
          new WorkPatternDay({
            day_of_week: "Friday",
            week_number: 1,
            minutes: 8 * 60,
          }),
          new WorkPatternDay({
            day_of_week: "Saturday",
            week_number: 1,
            minutes: 0,
          }),
        ],
      })
    );

    set(this.claimAttrs, "hours_worked_per_week", 40);

    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  variableWorkPattern() {
    const workPattern = WorkPattern.createWithWeek(40 * 60, {
      work_pattern_type: WorkPatternType.variable,
    });

    set(this.claimAttrs, "work_pattern", workPattern);
    set(this.claimAttrs, "hours_worked_per_week", 40);

    return this;
  }

  /**
   * @returns {Claim}
   */
  create() {
    return new Claim(this.claimAttrs);
  }
}

/**
 * Render a component, automatically setting its appLogic and query props
 * @example const { appLogic, wrapper } = renderWithAppLogic(MyPage)
 * @param {React.Component} PageComponent - the component you want to render
 * @param {object} [options]
 * @param {object} [options.claimAttrs] - Additional attributes to set on the Claim
 * @param {number} [options.diveLevels] - number of levels to dive before returning the enzyme wrapper.
 *    This is needed to return the desired component when the component is wrapped in higher-order components.
 *    Defaults to 2 since most claim pages are wrapped by `withUser(withClaim(Page))`.
 * @param {object} [options.props] - Additional props to set on the PageComponent
 * @param {"mount"|"shallow"} [options.render] - Enzyme render method. Shallow renders by default.
 * @param {object} [options.userAttrs] - Additional attributes to set on the User
 * @param {boolean} [options.hasLoadedClaimDocuments] - Additional attributes to indicate document loading is finished
 * @param {boolean} [options.hasUploadedCertificationDocuments] - Additional attributes to set certification documents
 * @param {boolean} [options.hasUploadedIdDocuments] - Additional attributes to set id documents
 * @param {boolean} [options.hasLoadingDocumentsError] - Additional attributs to set errors for loading documents
 * @param {boolean} [options.hasLegalNotices] - Create legal notices for claim
 * @param {object} [options.warningsLists] - Mock appLogic.claims.warningsLists
 * @returns {{ appLogic: object, claim: Claim, wrapper: object }}
 */
export const renderWithAppLogic = (PageComponent, options = {}) => {
  let appLogic, wrapper;
  options = merge(
    {
      claimAttrs: {},
      diveLevels: 2,
      employerClaimAttrs: {},
      props: {},

      // whether to use shallow() or mount()
      render: "shallow",
      userAttrs: {},
      warningsLists: {},
    },
    options
  );
  // Add claim and user instances to appLogic
  testHook(() => {
    appLogic = useAppLogic();
  });
  const claim = new Claim({
    application_id: "mock_application_id",
    ...options.claimAttrs,
  });
  appLogic.claims.claims = new ClaimCollection([claim]);
  appLogic.claims.hasLoadedClaimAndWarnings = jest
    .fn()
    .mockReturnValue(options.hasLoadedClaimAndWarnings || true);
  appLogic.claims.warningsLists = options.warningsLists;
  appLogic.employers.claim = new EmployerClaim(options.employerClaimAttrs);
  appLogic.auth.isLoggedIn = true;
  appLogic.users.requireUserConsentToDataAgreement = jest.fn();
  appLogic.users.user = new User({
    consented_to_data_sharing: true,
    user_id: "mock_user_id",
    ...options.userAttrs,
  });

  if (options.hasLoadedClaimDocuments) {
    appLogic.documents.hasLoadedClaimDocuments = jest
      .fn()
      .mockImplementation(() => true);
  }

  if (options.hasUploadedIdDocuments) {
    appLogic.documents.documents = appLogic.documents.documents.addItem(
      new Document({
        application_id: "mock_application_id",
        fineos_document_id: 1,
        document_type: DocumentType.identityVerification,
      })
    );
  }

  if (options.hasUploadedCertificationDocuments) {
    appLogic.documents.documents = appLogic.documents.documents.addItem(
      new Document({
        application_id: "mock_application_id",
        fineos_document_id: 2,
        document_type: DocumentType.medicalCertification,
      })
    );
  }

  if (options.hasLoadingDocumentsError) {
    appLogic.appErrors = new AppErrorInfoCollection([
      new AppErrorInfo({
        meta: { application_id: "mock_application_id" },
        name: "DocumentsRequestError",
      }),
    ]);
  }

  if (options.hasLegalNotices) {
    appLogic.documents.documents = appLogic.documents.documents.addItem(
      new Document({
        application_id: "mock_application_id",
        created_at: "2021-01-01",
        document_type: DocumentType.approvalNotice,
        fineos_document_id: 3,
      })
    );
  }

  // Render the withClaim-wrapped page
  const component = (
    <PageComponent
      appLogic={appLogic}
      query={{ claim_id: claim.application_id }}
      {...options.props}
    />
  );

  act(() => {
    // Go two levels deep to get the component that was wrapped by withUser and withClaim
    if (options.render === "shallow") {
      wrapper = shallow(component);
      times(options.diveLevels, () => {
        wrapper = wrapper.dive();
      });
    } else {
      wrapper = mount(component);
      times(options.diveLevels, () => {
        wrapper = wrapper.childAt(0);
      });
    }
  });

  return { appLogic, claim, wrapper };
};

/**
 * React functional component that is used to test React hooks,
 * which can only be called in the context of a functional component
 * @param {object} props React props
 * @param {Function} props.callback Function to run within the context of the TestHookComponent functional component
 * @returns {null}
 */
const TestHookComponent = (props) => {
  props.callback();
  return null;
};

/**
 * A function to aid in the testing of React hooks.
 * This function takes a callback that can execute the react hook within the callback.
 * testHook will ensure that the callback is executed in the context of a functional component,
 * which is necessary for React hooks.
 *
 * @example
 * testHook(() => {
 *   const x = useSomeCustomReactHook(); // this will be called inside a functional component
 * });
 *
 * @param {Function} callback Function that will get run in the context of a TestHookComponent
 */
export const testHook = (callback) => {
  mount(<TestHookComponent callback={callback} />);
};

/**
 * Make a File instance
 * @see https://developer.mozilla.org/en-US/docs/Web/API/File
 * @param {object} attrs File attributes
 * @param {string} attrs.name The file's name
 * @param {string} attrs.type The file's MIME type
 * @returns {File}
 */
export const makeFile = (attrs = {}) => {
  const { name, type } = Object.assign(
    {
      name: "file.pdf",
      type: "application/pdf",
    },
    attrs
  );

  return new File([], name, { type });
};

/**
 * Export convenience functions to simulate events like typing
 * into input fields and submitting forms, and run the simulated
 * events in Enzyme's `act` function to ensure any re-rendering
 * logic is run.
 * @example
 * let wrapper;
 * act(() => {
 *   wrapper = shallow(<Component />);
 * });
 * const { input, submitForm } = simulateEvents(wrapper);
 *
 * changeField("username", "jane.doe@test.com");
 * changeField("password", "P@ssw0rd");
 * submitForm();
 * @param {React.Component} wrapper React wrapper component
 * @returns {{ changeField: Function, submitForm: Function }}
 */
export const simulateEvents = (wrapper) => {
  /**
   * Simulate typing into an input field that lives within a component
   * @param {string} name Name of input field
   * @param {string} value Value for input field
   * @param {string?} [type] Type of form field
   * @param {boolean?} [checked] Whether the radio option / checkbox is selected
   */
  function changeField(name, value, type, checked) {
    act(() => {
      wrapper.find({ name }).simulate("change", {
        target: { checked, name, type, value },
      });
    });
  }

  /**
   * Simulate selecting an option that lives within a component
   * @param {string} name Name of input field
   * @param {string} value Value for input field
   */
  function changeRadioGroup(name, value) {
    act(() => {
      wrapper
        .find({ name })
        .last() // in cases where we use `mount` to render, we want the actual input component, which comes last in order
        .simulate("change", {
          target: { checked: true, name, type: "radio", value },
        });
    });
  }

  /**
   * Simulate selecting/deselecting a checkbox
   * @param {string} name Name of input field
   * @param {boolean} checked Select (true) or deselect (false)
   */
  function changeCheckbox(name, checked) {
    act(() => {
      const input = wrapper.find({ name }).last();
      const value = input.prop("value");

      input.simulate("change", {
        target: { checked, name, type: "checkbox", value },
      });
    });
  }

  /**
   * Simulate clicking on an element, such as a button or link
   * @param {*} enzymeSelector Enzyme selector. See https://enzymejs.github.io/enzyme/docs/api/selector.html
   */
  function click(enzymeSelector) {
    act(() => {
      wrapper.find(enzymeSelector).simulate("click", {
        preventDefault: jest.fn(),
      });
    });
  }

  /**
   * Simulate submitting a form contained within a component
   */
  function submitForm() {
    act(() => {
      wrapper.find("form").simulate("submit", {
        preventDefault: jest.fn(),
      });
    });
  }

  return { changeField, changeRadioGroup, click, changeCheckbox, submitForm };
};
