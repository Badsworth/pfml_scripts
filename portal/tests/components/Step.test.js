import { render, screen } from "@testing-library/react";
import React from "react";
import Step from "../../src/components/Step";

function getInitialProps() {
  return {
    stepHref: "/path-to-step-question",
    startText: "Start",
    resumeText: "Resume",
    resumeScreenReaderText: "Continue",
    completedText: "Completed",
    editText: "Edit",
    editable: true,
    screenReaderNumberPrefix: "Step",
    number: "1",
    title: "Step Title",
  };
}

describe("Step", () => {
  it("renders component", () => {
    const { container } = render(
      <Step {...getInitialProps()} status="not_started">
        <div>Description of step</div>
      </Step>
    );

    expect(container.firstChild).toMatchSnapshot();
  });

  it("shows children, displays start button when status is not_started", () => {
    const props = {
      ...getInitialProps(),
      status: "not_started",
    };
    render(
      <Step {...props}>
        <div>Description of step</div>
      </Step>
    );

    expect(screen.getByText("Description of step")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: `${props.startText}: ${props.title}` })
    ).toBeInTheDocument();
  });

  it("shows children, does not show action links when status is not_applicable", () => {
    render(
      <Step {...getInitialProps()} status="not_applicable">
        <div>Description of step</div>
      </Step>
    );

    expect(screen.getByText("Description of step")).toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("shows children, displays resume button when status is in_progress", () => {
    const props = {
      ...getInitialProps(),
      status: "in_progress",
    };
    render(
      <Step {...props}>
        <div>Description of step</div>
      </Step>
    );

    expect(screen.getByText("Description of step")).toBeInTheDocument();
    expect(
      screen.getByRole("link", {
        name: `${props.resumeScreenReaderText}: ${props.title}`,
      })
    ).toBeInTheDocument();
  });

  it("does not show children, shows completed and edit link when status is completed", () => {
    const props = {
      ...getInitialProps(),
      status: "completed",
    };
    render(
      <Step {...props}>
        <div>Description of step</div>
      </Step>
    );

    expect(screen.queryByText("Description of step")).not.toBeInTheDocument();
    expect(
      screen.getByRole("link", {
        name: `${props.editText}: ${props.title}`,
      })
    ).toBeInTheDocument();
    expect(screen.getByText(props.completedText)).toBeInTheDocument();
  });

  it("hides edit link if editable is false when status is completed", () => {
    render(
      <Step {...getInitialProps()} status="completed" editable={false}>
        <div>Description of step</div>
      </Step>
    );

    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("does not show children, shows a disabled start button when status is disabled", () => {
    const props = {
      ...getInitialProps(),
      status: "disabled",
    };
    render(
      <Step {...props}>
        <div>Description of step</div>
      </Step>
    );

    const button = screen.getByRole("button", {
      name: `${props.startText}: ${props.title}`,
    });

    expect(button).toBeDisabled();
    expect(screen.queryByText("Description of step")).not.toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });
});
