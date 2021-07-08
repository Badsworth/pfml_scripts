import { simulateEvents, testHook } from "../../test-utils";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import React from "react";
import SupportingWorkDetails from "../../../src/components/employers/SupportingWorkDetails";
import { shallow } from "enzyme";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

describe("SupportingWorkDetails", () => {
  const hoursWorkedPerWeek = 30;
  const updateFields = jest.fn();
  let getFunctionalInputProps;

  beforeEach(() => {
    testHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors: new AppErrorInfoCollection(),
        formState: { hours_worked_per_week: hoursWorkedPerWeek },
        updateFields,
      });
    });
  });

  function render() {
    return shallow(
      <SupportingWorkDetails
        getFunctionalInputProps={getFunctionalInputProps}
        initialHoursWorkedPerWeek={hoursWorkedPerWeek}
        updateFields={updateFields}
      />
    );
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

  function isElementVisible(element) {
    return element
      .parents("ConditionalContent")
      .everyWhere((el) => el.prop("visible") === true);
  }

  it("renders the component with the AmendmentForm closed", () => {
    const wrapper = render();
    expect(isElementVisible(wrapper.find("AmendmentForm"))).toBe(false);
    expect(wrapper).toMatchSnapshot();
  });

  it("renders the initial weekly hours in the ReviewRow", () => {
    const wrapper = render();
    expect(wrapper.find("p").first().text()).toEqual("30");
  });

  it("opens the AmendmentForm when the amend button is clicked", () => {
    const wrapper = render();

    clickAmendButton(wrapper);

    expect(isElementVisible(wrapper.find("AmendmentForm"))).toBe(true);
    expect(wrapper).toMatchSnapshot();
  });

  it("updates the form state on change", () => {
    const wrapper = render();
    clickAmendButton(wrapper);

    const { changeField } = simulateEvents(wrapper);
    changeField("hours_worked_per_week", 10);

    expect(updateFields).toHaveBeenCalledWith({ hours_worked_per_week: 10 });
  });

  describe("when amendment is canceled", () => {
    it("hides the amendment form", () => {
      const wrapper = render();
      clickAmendButton(wrapper);

      clickCancelAmendmentButton(wrapper);

      expect(isElementVisible(wrapper.find("AmendmentForm"))).toBe(false);
    });

    it("restores hours_worked_per_week to its intial value", () => {
      const wrapper = render();
      clickAmendButton(wrapper);
      const { changeField } = simulateEvents(wrapper);
      changeField("hours_worked_per_week", 10);

      clickCancelAmendmentButton(wrapper);

      expect(updateFields).toHaveBeenCalledTimes(2);
      expect(updateFields).toHaveBeenCalledWith({ hours_worked_per_week: 10 });
      expect(updateFields).toHaveBeenCalledWith({ hours_worked_per_week: 30 });
    });
  });
});
