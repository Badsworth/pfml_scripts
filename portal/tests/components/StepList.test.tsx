import { render, screen } from "@testing-library/react";
import React from "react";
import Step from "../../src/components/Step";
import StepList from "../../src/components/StepList";

function getInitialProps() {
  return {
    title: "Create an application",
    description: "Complete these steps.",
    startText: "Start",
    resumeText: "Resume",
    resumeScreenReaderText: "Continue",
    editText: "Edit",
    screenReaderNumberPrefix: "Step",
  };
}

describe("StepList", () => {
  it("renders component", () => {
    const { container } = render(
      <StepList {...getInitialProps()}>
        <Step
          editable
          title="Household info"
          stepHref="#household"
          status="not_started"
          completedText="Completed"
        >
          Enter details about your household.
        </Step>
      </StepList>
    );

    expect(container.firstChild).toMatchSnapshot();
  });

  it("passes *Text props set on the root to its Step children", () => {
    const props = getInitialProps();

    render(
      <StepList {...props}>
        <Step
          editable
          title="Household info"
          stepHref="#household"
          status="in_progress"
          completedText="Completed"
        >
          Enter details about your household.
        </Step>
        <Step
          editable
          title="Payment info"
          stepHref="#payment"
          status="completed"
          completedText="Completed"
        >
          How do you want paid?
        </Step>
      </StepList>
    );

    expect(screen.getByText(props.resumeText)).toBeInTheDocument();
    expect(screen.getByText(props.editText)).toBeInTheDocument();
  });

  it("does not override a Step number if one is defined", () => {
    const { container } = render(
      <StepList {...getInitialProps()}>
        <Step
          editable
          number={4}
          title="Upload documents"
          stepHref="#"
          status="not_started"
          completedText="Completed"
        >
          Step Description
        </Step>
      </StepList>
    );

    expect(container.firstChild).toContainHTML('aria-label="Step 4"');
  });
});
