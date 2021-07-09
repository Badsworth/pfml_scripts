import { act } from "react-dom/test-utils";
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
 * await submitForm();
 * @param {React.Component} wrapper React wrapper component
 * @returns {{ changeField: Function, submitForm: Function }}
 */
const simulateEvents = (wrapper) => {
  /**
   * Simulate typing into an input field that lives within a component
   * @param {string} name Name of input field
   * @param {string} value Value for input field
   * @param {string?} [type] Type of form field
   * @param {boolean?} [checked] Whether the radio option / checkbox is selected
   */
  function changeField(name, value, type, checked) {
    act(() => {
      wrapper
        .find({ name })
        .last() // in cases where we use `mount` to render, we want the actual input component, which comes last in order
        .simulate("change", {
          target: { checked, name, type, value, getAttribute: jest.fn() },
        });
    });
  }

  /**
   * Simulate selecting an option that lives within a component
   * @param {string} name Name of input field
   * @param {string} value Value for input field
   * @param {string} [id] ID attribute for input field
   */
  function changeRadioGroup(name, value, id) {
    act(() => {
      wrapper
        .find({ name })
        .last() // in cases where we use `mount` to render, we want the actual input component, which comes last in order
        .simulate("change", {
          target: {
            checked: true,
            id,
            name,
            type: "radio",
            value,
            getAttribute: jest.fn(),
          },
        });
    });
  }

  /**
   * Simulate selecting/deselecting a checkbox
   * @param {string} name Name of input field
   * @param {boolean} checked Select (true) or deselect (false)
   * @param {string} [value] of the checkbox
   */
  function changeCheckbox(name, checked, value) {
    act(() => {
      const input = wrapper.find({ name }).last();

      input.simulate("change", {
        target: {
          checked,
          name,
          type: "checkbox",
          value,
          getAttribute: jest.fn(),
        },
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
   * @returns {Promise}
   */
  async function submitForm() {
    let eventName, form;

    const formComponent = wrapper.find("form");
    if (formComponent.exists()) {
      form = formComponent;
      eventName = "submit";
    } else {
      form = wrapper.find("QuestionPage");
      eventName = "save";
    }

    await act(async () => {
      await form.simulate(eventName, {
        preventDefault: jest.fn(),
      });
    });
  }

  return { changeField, changeRadioGroup, click, changeCheckbox, submitForm };
};

export default simulateEvents;
