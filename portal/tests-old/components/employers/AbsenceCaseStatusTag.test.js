import AbsenceCaseStatusTag from "../../../src/components/AbsenceCaseStatusTag";
import React from "react";
import { shallow } from "enzyme";

describe("AbsenceCaseStatusTag", () => {
  beforeEach(() => {
    process.env.featureFlags = {
      employerShowReviewByStatus: true,
    };
  });

  const renderComponent = (status, managedRequirements) => {
    return shallow(
      <AbsenceCaseStatusTag
        status={status}
        managedRequirements={managedRequirements}
      />
    );
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

  it("renders the component with 'Review By {{date}}' when managedRequirements is not empty", () => {
    const managedRequirementsData = [
      { follow_up_date: "2021-08-22" },
      { follow_up_date: "2021-07-22" },
    ];
    const wrapper = renderComponent("Approved", managedRequirementsData);

    expect(wrapper).toMatchSnapshot();
  });

  it("renders the component with 'No Action Required' when managedRequirements is empty and has a pending-line status value", () => {
    const managedRequirementsData = [];
    const wrapper = renderComponent(
      "Intake In Progress",
      managedRequirementsData
    );

    expect(wrapper).toMatchSnapshot();
  });

  it("renders -- for invalid status values", () => {
    process.env.featureFlags = {
      employerShowReviewByStatus: false,
    };

    const wrapperWithPendingState = renderComponent("Pending", []);
    const wrapperWithEmptyState = renderComponent("", []);

    expect(wrapperWithPendingState.text()).toEqual("--");
    expect(wrapperWithEmptyState.text()).toEqual("--");
  });
});
