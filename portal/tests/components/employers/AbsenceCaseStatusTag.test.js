import AbsenceCaseStatusTag from "../../../src/components/AbsenceCaseStatusTag";
import React from "react";
import { shallow } from "enzyme";

describe("AbsenceCaseStatusTag", () => {
  const renderComponent = (status) => {
    return shallow(<AbsenceCaseStatusTag status={status} />);
  };

  it("renders the component with success state for 'Approved'", () => {
    const wrapper = renderComponent("Approved");

    expect(wrapper).toMatchSnapshot();
  });

  it("renders the component with error state and mapped status for 'Declined'", () => {
    const wrapper = renderComponent("Declined");

    expect(wrapper).toMatchSnapshot();
  });

  it("renders the component with inactive state for 'Closed'", () => {
    const wrapper = renderComponent("Closed");

    expect(wrapper).toMatchSnapshot();
  });

  it("renders the component with inactive state and mapped status for 'Completed'", () => {
    const wrapper = renderComponent("Completed");

    expect(wrapper).toMatchSnapshot();
  });

  it("renders -- for invalid status values", () => {
    const wrapperWithPendingState = renderComponent("Pending");
    const wrapperWithEmptyState = renderComponent("");

    expect(wrapperWithPendingState.text()).toEqual("--");
    expect(wrapperWithEmptyState.text()).toEqual("--");
  });
});
