import { render, screen } from "@testing-library/react";
import { ChecklistAlerts } from "../../src/pages/applications/checklist";
import React from "react";

const renderComponent = (customProps = {}) => {
  const props = {
    submitted: "partOne",
    ...customProps,
  };
  return render(<ChecklistAlerts {...props} />);
};

describe("ChecklistAlerts", () => {
  it("renders part one submitted when indicated", () => {
    renderComponent({
      query: {
        claim_id: "mock-application-id",
        "part-one-submitted": "true",
      },
    });
    expect(
      screen.getByText(
        "You successfully submitted Part 1. Submit Parts 2 and 3 so that we can review your application."
      )
    ).toBeInTheDocument();
  });

  it("If payment just submitted renders payment alert", () => {
    renderComponent({
      submitted: "payment",
    });
    expect(
      screen.getByText(
        "You successfully submitted your payment method. Complete the remaining steps so that you can submit your application."
      )
    ).toBeInTheDocument();
  });

  it("If tax just submitted, renders tax alert", () => {
    renderComponent({
      submitted: "taxPref",
    });
    expect(
      screen.getByText(
        "You successfully submitted your tax withholding preference. Complete the remaining steps so that you can submit your application."
      )
    ).toBeInTheDocument();
  });
});
