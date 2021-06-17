import AmendButton from "../../../src/components/employers/AmendButton";
import AmendableConcurrentLeave from "../../../src/components/employers/AmendableConcurrentLeave";
import AmendmentForm from "../../../src/components/employers/AmendmentForm";
import Button from "../../../src/components/Button";
import ConcurrentLeave from "../../../src/models/ConcurrentLeave";
import InputDate from "../../../src/components/InputDate";
import React from "react";
import { shallow } from "enzyme";
import { testHook } from "../../test-utils";
import useAppLogic from "../../../src/hooks/useAppLogic";

describe("AmendableConcurrentLeave", () => {
  const concurrentLeave = new ConcurrentLeave({
    leave_start_date: "2020-03-01",
    leave_end_date: "2020-03-06",
  });
  const onChange = jest.fn();

  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });

    wrapper = shallow(
      <AmendableConcurrentLeave
        appErrors={appLogic.appErrors}
        concurrentLeave={concurrentLeave}
        onChange={onChange}
      />
    );
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("renders an AmendmentForm if user clicks on AmendButton", () => {
    wrapper.find(AmendButton).simulate("click");

    expect(wrapper.find(AmendmentForm).exists()).toEqual(true);
  });

  it("updates start and end dates in the AmendmentForm", () => {
    wrapper.find(AmendButton).simulate("click");
    wrapper
      .find(InputDate)
      .first()
      .simulate("change", { target: { value: "2020-10-10" } });
    wrapper
      .find(InputDate)
      .last()
      .simulate("change", { target: { value: "2020-10-20" } });

    expect(onChange).toHaveBeenCalledTimes(2);
    expect(wrapper.find(InputDate).first().prop("value")).toEqual("2020-10-10");
    expect(wrapper.find(InputDate).last().prop("value")).toEqual("2020-10-20");
  });

  it("restores original value on cancel", () => {
    wrapper.find(AmendButton).simulate("click");
    wrapper
      .find(InputDate)
      .first()
      .simulate("change", { target: { value: "2020-10-10" } });

    expect(wrapper.find(InputDate).first().prop("value")).toEqual("2020-10-10");

    wrapper.find(AmendmentForm).dive().find(Button).simulate("click");

    wrapper.find(AmendButton).simulate("click");
    expect(wrapper.find(InputDate).first().prop("value")).toEqual("2020-03-01");
  });
});
