import { render, screen } from "@testing-library/react";
import CaringLeaveQuestion from "src/features/employer-review/CaringLeaveQuestion";
import React from "react";
import userEvent from "@testing-library/user-event";

describe("CaringLeaveQuestion", () => {
  function renderComponent(customProps = {}) {
    const defaultProps = {
      errorMsg: null,
      believeRelationshipAccurate: undefined,
      onChangeBelieveRelationshipAccurate: jest.fn(),
      onChangeRelationshipInaccurateReason: jest.fn(),
      ...customProps,
    };
    return render(<CaringLeaveQuestion {...defaultProps} />);
  }

  it("renders the component", () => {
    const { container } = renderComponent();
    expect(container.firstChild).toMatchSnapshot();
  });

  it("initially renders with all conditional comment boxes hidden", () => {
    renderComponent();
    expect(screen.queryByTestId("inaccurate_reason")).not.toBeInTheDocument();
  });

  it("calls onChangeBelieveRelationshipAccurate when user changes the relation answer", () => {
    const onChangeMock = jest.fn();
    renderComponent({
      onChangeBelieveRelationshipAccurate: onChangeMock,
    });

    userEvent.click(screen.getByRole("radio", { name: "I don't know" }));

    expect(onChangeMock).toHaveBeenCalledWith("Unknown");
  });

  it("renders the comment box and the alert when user indicates the relationship is inaccurate ", () => {
    renderComponent({
      believeRelationshipAccurate: "No",
    });

    expect(screen.getByTestId("inaccurate_reason")).toBeInTheDocument();
    expect(screen.getByRole("region")).toMatchSnapshot();
  });

  it("calls onChangeRelationshipInaccurateReason when user leaves a comment", () => {
    const onChangeMock = jest.fn();
    renderComponent({
      believeRelationshipAccurate: "No",
      onChangeRelationshipInaccurateReason: onChangeMock,
    });

    userEvent.type(screen.getByRole("textbox"), "This is a comment");

    expect(onChangeMock).toHaveBeenCalledWith("This is a comment");
  });

  it("renders the alert info when user indicates the relationship status is unknown ", () => {
    renderComponent({
      believeRelationshipAccurate: "Unknown",
    });

    expect(screen.getByRole("region")).toMatchSnapshot();
  });

  it("renders inline error message when the text exceeds the limit", () => {
    renderComponent({
      believeRelationshipAccurate: "No",
      errorMsg:
        "Please shorten your comment. We cannot accept comments that are longer than 9999 characters.",
    });

    expect(
      screen.getByRole("textbox", {
        name: "Tell us why you think this relationship is inaccurate.",
      })
    ).toHaveClass("usa-input--error");
    expect(screen.getByTestId("inaccurate_reason")).toMatchSnapshot();
  });
});
