import Claim, {
  ContinuousLeavePeriod,
  IntermittentLeavePeriod,
  ReducedScheduleLeavePeriod,
} from "../src/models/Claim";
import { mount, shallow } from "enzyme";
import ClaimCollection from "../src/models/ClaimCollection";
import React from "react";
import User from "../src/models/User";
import { act } from "react-dom/test-utils";
import merge from "lodash/merge";
import set from "lodash/set";
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
  continuous() {
    set(
      this.claimAttrs,
      "temp.leave_details.continuous_leave_periods[0]",
      new ContinuousLeavePeriod()
    );
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  intermittent() {
    set(
      this.claimAttrs,
      "leave_details.intermittent_leave_periods[0]",
      new IntermittentLeavePeriod()
    );
    return this;
  }

  /**
   * @returns {MockClaimBuilder}
   */
  reducedSchedule() {
    set(
      this.claimAttrs,
      "temp.leave_details.reduced_schedule_leave_periods[0]",
      new ReducedScheduleLeavePeriod()
    );
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
 * @param {object} options.claimAttrs - Additional attributes to set on the Claim
 * @param {object} options.props - Additional props to set on the PageComponent
 * @param {"mount"|"shallow"} options.render - Enzyme render method. Shallow renders by default.
 * @param {object} options.userAttrs - Additional attributes to set on the User
 * @returns {{ appLogic: object, claim: Claim, wrapper: object }}
 */
export const renderWithAppLogic = (PageComponent, options = {}) => {
  let appLogic, wrapper;
  options = merge(
    { claimAttrs: {}, props: {}, render: "shallow", userAttrs: {} },
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
  appLogic.users.user = new User({
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
    // Go one level deep to get the component that was wrapped by withClaim
    if (options.render === "shallow") {
      wrapper = shallow(component).dive();
    } else {
      wrapper = mount(component).childAt(0);
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
   * @param {strign} value Value for input field
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
