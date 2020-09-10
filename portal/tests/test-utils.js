import Claim, {
  ClaimStatus,
  ContinuousLeavePeriod,
  DurationBasis,
  EmploymentStatus,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
  LeaveReason,
  PaymentPreferenceMethod,
  ReasonQualifier,
  ReducedScheduleLeavePeriod,
} from "../src/models/Claim";
import EmployerBenefit, {
  EmployerBenefitType,
} from "../src/models/EmployerBenefit";
import { mount, shallow } from "enzyme";
import Address from "../src/models/Address";
import ClaimCollection from "../src/models/ClaimCollection";
import PreviousLeave from "../src/models/PreviousLeave";
import React from "react";
import User from "../src/models/User";
import { act } from "react-dom/test-utils";
import merge from "lodash/merge";
import set from "lodash/set";
import times from "lodash/times";
import useAppLogic from "../src/hooks/useAppLogic";

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
export class MockClaimBuilder {
  constructor() {
    this.claimAttrs = { application_id: "mock_application_id" };
  }

  /**
   * @returns {MockClaimBuilder}
   */
  id(application_id) {
    set(this.claimAttrs, "application_id", application_id);
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  continuous(attrs = {}) {
    set(
      this.claimAttrs,
      "temp.leave_details.continuous_leave_periods[0]",
      new ContinuousLeavePeriod(attrs)
    );

    // TODO (CP-720): These are the only fields currently available in the API
    // remove once continuous leave is fully integrated with API
    const { leave_period_id, start_date, end_date } = attrs;

    set(this.claimAttrs, "leave_details.continuous_leave_periods[0]", {
      leave_period_id,
      start_date,
      end_date,
    });
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
   * @returns {MockClaimBuilder}
   */
  intermittent(attrs) {
    set(
      this.claimAttrs,
      "leave_details.intermittent_leave_periods[0]",
      new IntermittentLeavePeriod(attrs)
    );
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  reducedSchedule(attrs = {}) {
    set(
      this.claimAttrs,
      "temp.leave_details.reduced_schedule_leave_periods[0]",
      new ReducedScheduleLeavePeriod(attrs)
    );

    // TODO (CP-714): These are the only fields currently available in the API
    // remove once reduced leave is fully integrated with API
    const { leave_period_id, start_date, end_date } = attrs;

    set(this.claimAttrs, "leave_details.reduced_schedule_leave_periods[0]", {
      leave_period_id,
      start_date,
      end_date,
    });
    return this;
  }

  bondingBirthLeaveReason(attrs = { birthdate: "2012-02-12" }) {
    const { birth_date } = attrs;
    set(this.claimAttrs, "leave_details.reason", LeaveReason.bonding);
    set(
      this.claimAttrs,
      "leave_details.reason_qualifier",
      ReasonQualifier.newBorn
    );
    set(this.claimAttrs, "leave_details.child_birth_date", birth_date);
    return this;
  }

  bondingAdoptionLeaveReason(attrs = { birthdate: "2012-02-14" }) {
    const { placement_date } = attrs;
    set(this.claimAttrs, "leave_details.reason", LeaveReason.bonding);
    set(
      this.claimAttrs,
      "leave_details.reason_qualifier",
      ReasonQualifier.adoption
    );
    set(this.claimAttrs, "leave_details.child_placement_date", placement_date);
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  employed() {
    set(this.claimAttrs, "employment_status", EmploymentStatus.employed);
    set(this.claimAttrs, "employer_fein", "*********");
    set(this.claimAttrs, "leave_details.employer_notified", true);
    set(
      this.claimAttrs,
      "leave_details.employer_notification_date",
      "2021-01-01"
    );
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  medicalLeaveReason() {
    set(this.claimAttrs, "leave_details.reason", LeaveReason.medical);
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  noOtherLeave() {
    set(this.claimAttrs, "has_employer_benefits", false);
    set(this.claimAttrs, "has_other_incomes", false);
    set(this.claimAttrs, "has_previous_leaves", false);
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
    return this;
  }

  /**
   * All required data is present but the claim hasn't been marked
   * as Completed yet in the API
   * @returns {MockClaimBuilder}
   */
  complete() {
    this.submitted();

    set(
      this.claimAttrs,
      "temp.payment_preferences[0].payment_method",
      PaymentPreferenceMethod.ach
    );
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
   * Part 1 steps are complete and submitted to API
   * @returns {MockClaimBuilder}
   */
  submitted() {
    this.verifiedId();
    this.medicalLeaveReason();
    this.continuous();
    this.employed();
    this.noOtherLeave();
    this.address();
    this.leaveDuration();
    set(this.claimAttrs, "status", ClaimStatus.submitted);

    return this;
  }

  /**
   * @param {object} attrs Address object
   * @returns {MockClaimBuilder}
   */
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

  /**
   * @returns {MockClaimBuilder}
   */
  leaveDuration() {
    set(this.claimAttrs, "temp.start_date", "2021-01-01");
    set(this.claimAttrs, "temp.end_date", "2021-06-01");
    return this;
  }

  /**
   * @param {Array} attrs List of PreviousLeave objects
   * @returns {MockClaimBuilder}
   */
  previousLeave(attrs) {
    set(
      this.claimAttrs,
      "previous_leaves",
      attrs.map((attr) => new PreviousLeave(attr))
    );
    return this;
  }

  /**
   * @param {Array} attrs List of EmployerBenefit objects
   * @returns {MockClaimBuilder}
   */
  employerBenefit(attrs) {
    set(
      this.claimAttrs,
      "employer_benefits",
      attrs.map((attr) => new EmployerBenefit(attr))
    );
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  verifiedId() {
    set(this.claimAttrs, "first_name", "Jane");
    set(this.claimAttrs, "middle_name", "");
    set(this.claimAttrs, "last_name", "Doe");
    set(this.claimAttrs, "date_of_birth", "1980-07-17");
    set(this.claimAttrs, "tax_identifier", "***-**-****");
    this.address();
    this.hasStateId();
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
 * A complete mock claim (currently used for Employer Claim Review page & tests)
 * @type {Claim}
 */
export const claim = new MockClaimBuilder()
  .id(1)
  .verifiedId()
  .address()
  .medicalLeaveReason()
  .leaveDuration()
  .employed()
  .continuous({
    leave_period_id: 1,
    weeks: 12,
  })
  .intermittent({
    leave_period_id: 3,
    duration: 3,
    duration_basis: DurationBasis.hours,
    frequency: 6,
    frequency_interval: 6,
    frequency_interval_basis: FrequencyIntervalBasis.months,
  })
  .reducedSchedule({
    leave_period_id: 2,
    hours_per_week: 5,
    weeks: 10,
  })
  .previousLeave([
    {
      leave_start_date: "2020-03-01",
      leave_end_date: "2020-03-06",
    },
    {
      leave_start_date: "2020-03-01",
      leave_end_date: "2020-03-06",
    },
  ])
  .employerBenefit([
    {
      benefit_type: EmployerBenefitType.paidLeave,
    },
    {
      benefit_amount_dollars: 1000,
      benefit_end_date: "2021-03-01",
      benefit_start_date: "2021-02-01",
      benefit_type: EmployerBenefitType.shortTermDisability,
    },
    {
      benefit_type: EmployerBenefitType.permanentDisability,
    },
    {
      benefit_type: EmployerBenefitType.familyOrMedicalLeave,
    },
  ])
  .create();

/**
 * Render a component, automatically setting its appLogic and query props
 * @example const { appLogic, wrapper } = renderWithAppLogic(MyPage)
 * @param {React.Component} PageComponent - the component you want to render
 * @param {object} [options]
 * @param {object} [options.claimAttrs] - Additional attributes to set on the Claim
 * @param {number} [options.diveLevels] - number of levels to dive before returning the enzyme wrapper.
 *    This is needed to return the desired component when the component is wrapped in higher-order components.
 *    Defaults to 3 since most claim pages are wrapped by `withUser(withClaims(withClaim(Page)))`.
 * @param {object} [options.props] - Additional props to set on the PageComponent
 * @param {"mount"|"shallow"} [options.render] - Enzyme render method. Shallow renders by default.
 * @param {object} [options.userAttrs] - Additional attributes to set on the User
 * @returns {{ appLogic: object, claim: Claim, wrapper: object }}
 */
export const renderWithAppLogic = (PageComponent, options = {}) => {
  let appLogic, wrapper;
  options = merge(
    {
      claimAttrs: {},
      diveLevels: 3,
      props: {},

      // whether to use shallow() or mount()
      render: "shallow",
      userAttrs: {},
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
  appLogic.auth.isLoggedIn = true;
  appLogic.users.user = new User({
    consented_to_data_sharing: true,
    user_id: "mock_user_id",
    ...options.userAttrs,
  });

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
   * Simulate typing into an input field that lives within a component
   * @param {string} name Name of input field
   * @param {string} value Value for input field
   */
  function changeRadioGroup(name, value) {
    changeField(name, value, "radio", true);
  }

  /**
   * Simulate clicking on an element, such as a button or link
   * @param {*} enzymeSelector Enzym selector. See https://enzymejs.github.io/enzyme/docs/api/selector.html
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

  return { changeField, changeRadioGroup, click, submitForm };
};
