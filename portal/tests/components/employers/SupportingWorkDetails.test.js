import { mount, shallow } from "enzyme";
import { simulateEvents, testHook } from "../../test-utils";
import AppErrorInfo from "../../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import React from "react";
import SupportingWorkDetails from "../../../src/components/employers/SupportingWorkDetails";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

describe("SupportingWorkDetails", () => {
  const appErrors = new AppErrorInfoCollection();
  const hoursWorkedPerWeek = 30;
  const getField = jest.fn();
  const clearField = jest.fn();
  const updateFields = jest.fn();
  let getFunctionalInputProps;

  beforeEach(() => {
    testHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors,
        formState: { hours_worked_per_week: hoursWorkedPerWeek },
        updateFields,
      });
    });
  });

  function render(renderMode = "shallow", givenProps = {}) {
    const defaultProps = {
      appErrors,
      clearField,
      getField,
      getFunctionalInputProps,
      initialHoursWorkedPerWeek: hoursWorkedPerWeek,
      updateFields,
    };
    const props = { ...defaultProps, ...givenProps };
    if (renderMode === "mount") {
      return mount(<SupportingWorkDetails {...props} />);
    }
    return shallow(<SupportingWorkDetails {...props} />);
  }

  function clickAmendButton(wrapper) {
    wrapper.find("ReviewRow").dive(3).find("AmendButton").simulate("click");
  }

  function clickCancelAmendmentButton(wrapper) {
    wrapper
      .find("AmendmentForm")
      .dive()
      .find({ "data-test": "amendment-destroy-button" })
      .simulate("click");
  }

  function isAmendmentFormVisible(wrapper) {
    return wrapper.find("ConditionalContent").prop("visible") === true;
  }

  it("renders the component with the AmendmentForm hidden", () => {
    const wrapper = render();
    expect(isAmendmentFormVisible(wrapper)).toBe(false);
    expect(wrapper).toMatchSnapshot();
  });

  it("forces open the amendment form if there is an error", () => {
    const appErrors = new AppErrorInfoCollection([
      new AppErrorInfo({
        field: "hours_worked_per_week",
        message: "New error",
      }),
    ]);
    testHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors,
        formState: { hours_worked_per_week: 30 },
        updateFields,
      });
    });
    const wrapper = render("mount", { appErrors });

    expect(isAmendmentFormVisible(wrapper)).toBe(true);
  });

  it("renders the initial weekly hours in the ReviewRow", () => {
    const wrapper = render();
    expect(wrapper.find("p").first().text()).toEqual("30");
  });

  it("opens the AmendmentForm when the amend button is clicked", () => {
    const wrapper = render();

    clickAmendButton(wrapper);

    expect(isAmendmentFormVisible(wrapper)).toBe(true);
  });

  it("updates the form state on change", () => {
    const wrapper = render();
    clickAmendButton(wrapper);

    const { changeField } = simulateEvents(wrapper);
    changeField("hours_worked_per_week", 10);

    expect(updateFields).toHaveBeenCalledWith({ hours_worked_per_week: 10 });
  });

  it("allows closing the amendment form if there is an error", () => {
    const appErrors = new AppErrorInfoCollection([
      new AppErrorInfo({
        field: "hours_worked_per_week",
        message: "New error",
      }),
    ]);
    testHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors,
        formState: { hours_worked_per_week: 30 },
        updateFields,
      });
    });
    const wrapper = render("mount", { appErrors });

    expect(isAmendmentFormVisible(wrapper)).toBe(true);
    wrapper.find({ "data-test": "amendment-destroy-button" }).simulate("click");
    expect(wrapper.find("AmendmentForm").exists()).toBe(false);
  });

  describe("when amendment is canceled", () => {
    it("hides the amendment form", () => {
      const wrapper = render();
      clickAmendButton(wrapper);
      expect(isAmendmentFormVisible(wrapper)).toBe(true);

      clickCancelAmendmentButton(wrapper);

      expect(isAmendmentFormVisible(wrapper)).toBe(false);
    });

    it("clears hours_worked_per_week", () => {
      const wrapper = render("mount");
      wrapper.find({ "data-test": "amend-button" }).simulate("click");
      wrapper
        .find({ "data-test": "amendment-destroy-button" })
        .simulate("click");

      expect(clearField).toHaveBeenCalledWith("hours_worked_per_week");
    });
  });
});
