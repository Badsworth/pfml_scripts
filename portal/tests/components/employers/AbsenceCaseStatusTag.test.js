import { AbsenceCaseStatus } from "../../../src/models/Claim";
import AbsenceCaseStatusTag from "../../../src/components/AbsenceCaseStatusTag";
import React from "react";
import { render } from "@testing-library/react";

describe("AbsenceCaseStatusTag", () => {
  const renderComponent = (status, managedRequirements) => {
    return render(
      <AbsenceCaseStatusTag
        status={status}
        managedRequirements={managedRequirements}
      />
    );
  };

  it("renders the component with success state for 'Approved'", () => {
    const { container } = renderComponent(AbsenceCaseStatus.approved);

    expect(container).toMatchSnapshot();
  });

  it("renders the component with error state and mapped status for 'Declined'", () => {
    const { container } = renderComponent("Declined");

    expect(container).toMatchSnapshot();
  });

  it("renders the component with inactive state for 'Closed'", () => {
    const { container } = renderComponent(AbsenceCaseStatus.closed);

    expect(container).toMatchSnapshot();
  });

  it("renders the component with inactive state and mapped status for 'Completed'", () => {
    const { container } = renderComponent(AbsenceCaseStatus.completed);

    expect(container).toMatchSnapshot();
  });

  it("renders the component with 'Review By {{date}}' when managedRequirements is not empty", () => {
    process.env.featureFlags = { employerShowReviewByStatus: true };
    const managedRequirementsData = [
      { follow_up_date: "2021-08-22" },
      { follow_up_date: "2021-07-22" },
    ];
    const { container } = renderComponent(
      AbsenceCaseStatus.approved,
      managedRequirementsData
    );

    expect(container).toMatchSnapshot();
  });

  it("renders the component with '--' when managedRequirements is not empty, but Review By feature flag is not enabled", () => {
    const managedRequirementsData = [
      { follow_up_date: "2021-08-22" },
      { follow_up_date: "2021-07-22" },
    ];
    const { container } = renderComponent(
      AbsenceCaseStatus.approved,
      managedRequirementsData
    );

    expect(container).toHaveTextContent("--");
  });

  it("renders the component with 'No Action Required' when managedRequirements is empty and has a pending-line status value", () => {
    process.env.featureFlags = { employerShowReviewByStatus: true };
    const managedRequirementsData = [];
    const { container } = renderComponent(
      "Intake In Progress",
      managedRequirementsData
    );

    expect(container).toMatchSnapshot();
  });

  it("renders -- for invalid status values", () => {
    process.env.featureFlags = {
      employerShowReviewByStatus: false,
    };

    expect(renderComponent("Pending", []).container).toHaveTextContent("--");
    expect(renderComponent("", []).container).toHaveTextContent("--");
  });
});
