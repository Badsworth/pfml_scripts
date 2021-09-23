import { render, screen, within } from "@testing-library/react";
import AppErrorInfo from "../../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import Feedback from "../../../src/components/employers/Feedback";
import React from "react";
import { renderHook } from "@testing-library/react-hooks";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

jest.mock("../../../src/hooks/useAppLogic");

describe("Feedback", () => {
  const updateFields = jest.fn();
  let getFunctionalInputProps;

  const renderComponent = (customProps = {}) => {
    const defaultProps = {
      context: "",
      getFunctionalInputProps,
      shouldDisableNoOption: false,
      shouldShowCommentBox: false,
      ...customProps,
    };

    return render(<Feedback {...defaultProps} />);
  };

  function setUpFunctionalInputProps(customArgs = {}) {
    const defaultArgs = {
      appErrors: new AppErrorInfoCollection(),
      formState: {},
      updateFields,
    };
    const args = { ...defaultArgs, ...customArgs };
    renderHook(() => {
      getFunctionalInputProps = useFunctionalInputProps(args);
    });
  }

  beforeEach(() => {
    setUpFunctionalInputProps();
  });

  it("renders the component", () => {
    const { container } = renderComponent();
    expect(container.firstChild).toMatchSnapshot();
  });

  it("disables the 'No' option based on 'shouldDisableNoOption' prop", () => {
    renderComponent({
      shouldDisableNoOption: true,
      shouldShowCommentBox: true,
    });

    expect(screen.getByRole("radio", { name: "No" })).toBeDisabled();
  });

  it("when 'shouldShowCommentBox' is true, it shows the comment box", () => {
    renderComponent({ shouldShowCommentBox: true });
    expect(
      screen.getByRole("textbox", { name: "Please tell us more." })
    ).toBeInTheDocument();
  });

  it("when 'shouldShowCommentBox' is true, displays the correct default help message", () => {
    renderComponent({ shouldShowCommentBox: true });
    expect(screen.getByText(/Please tell us more./)).toBeInTheDocument();
  });

  it("Comment box displays the correct help message for 'fraud' context ", () => {
    renderComponent({
      shouldShowCommentBox: true,
      context: "fraud",
    });
    expect(
      screen.getByText(/Please tell us why you believe this is fraudulent./)
    ).toBeInTheDocument();
  });

  it("displays the correct help message for 'employerDecision' context", () => {
    renderComponent({
      shouldShowCommentBox: true,
      context: "employerDecision",
    });
    expect(
      screen.getByText(/Please tell us why you denied this leave request./)
    ).toBeInTheDocument();
  });

  it("displays the correct help message for 'employeeNotice' context", () => {
    renderComponent({
      shouldShowCommentBox: true,
      context: "employeeNotice",
    });
    expect(
      screen.getByText(
        /Please tell us when your employee notified you about their leave./
      )
    ).toBeInTheDocument();
  });

  it("renders inline error message when the text exceeds the limit", () => {
    renderHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors: new AppErrorInfoCollection([
          new AppErrorInfo({
            field: "comment",
            type: "maxLength",
            message:
              "Please shorten your comment. We cannot accept comments that are longer than 9999 characters.",
          }),
        ]),
        formState: {},
        updateFields,
      });
    });
    renderComponent({
      getFunctionalInputProps,
      shouldShowCommentBox: true,
    });
    expect(
      within(screen.getByRole("alert")).getByText(
        /Please shorten your comment. We cannot accept comments that are longer than 9999 characters./
      )
    ).toBeInTheDocument();
    expect(screen.getByRole("textbox")).toHaveClass("usa-input--error");
  });
});
