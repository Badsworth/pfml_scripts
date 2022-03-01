import { render, screen } from "@testing-library/react";
import ErrorInfo from "../../src/models/ErrorInfo";
import ErrorsSummary from "../../src/components/ErrorsSummary";
import React from "react";
import { Trans } from "react-i18next";

const renderComponent = (customProps) => {
  customProps = {
    errors: [new ErrorInfo({ message: "Mock error message" })],
    ...customProps,
  };
  return render(<ErrorsSummary {...customProps} />);
};

describe("ErrorsSummary", () => {
  it("does not render an alert when no errors exist", () => {
    renderComponent({ errors: [] });

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  describe("when only one error exists", () => {
    it("renders the singular heading and error message", () => {
      const { container } = renderComponent();

      expect(container.firstChild).toMatchInlineSnapshot(`
        <div
          aria-labelledby="alert-heading3"
          class="usa-alert usa-alert--error margin-bottom-3"
          role="alert"
          tabindex="-1"
        >
          <div
            class="usa-alert__body"
          >
            <h2
              class="usa-alert__heading font-heading-md text-bold"
              id="alert-heading3"
            >
              An error occurred
            </h2>
            <div
              class="usa-alert__text"
            >
              <p>
                Mock error message
              </p>
            </div>
          </div>
        </div>
      `);
    });

    it("renders a Trans component", () => {
      const errors = [
        new ErrorInfo({ message: <Trans i18nKey="errors.caughtError" /> }),
      ];

      renderComponent({ errors });

      expect(
        screen.getByText(
          "Sorry, an unexpected error in our system was encountered. If this continues to happen, you may call the Paid Family Leave Contact Center at (833) 344‑7365."
        )
      ).toBeInTheDocument();
    });
  });

  describe("when more than one error exists", () => {
    it("renders the plural heading and list of error messages", () => {
      const errors = [
        new ErrorInfo({ message: "Mock error message #1" }),
        new ErrorInfo({ message: "Mock error message #2" }),
      ];

      renderComponent({ errors });

      expect(screen.getByText("2 errors occurred")).toBeInTheDocument();
      expect(screen.queryAllByRole("listitem")).toHaveLength(2);
    });

    it("renders the singular heading if all errors are duplicates", () => {
      const errors = [
        new ErrorInfo({ message: "Mock error message #1" }),
        new ErrorInfo({ message: "Mock error message #1" }),
        new ErrorInfo({ message: "Mock error message #1" }),
      ];

      renderComponent({ errors });

      expect(screen.getByText("An error occurred")).toBeInTheDocument();
    });

    it("removes any duplicate error messages", () => {
      const errors = [
        new ErrorInfo({ message: "Mock error message #1" }),
        new ErrorInfo({ message: "Mock error message #1" }),
        new ErrorInfo({ message: "Mock error message #2" }),
      ];
      renderComponent({ errors });

      expect(screen.queryAllByRole("listitem")).toHaveLength(2);

      const listContainer = screen.getByRole("list");

      expect(listContainer.firstChild).toHaveTextContent(errors[0].message);
      expect(listContainer.lastChild).toHaveTextContent(errors[2].message);
    });

    it("renders elements corresponding to text in Trans components", () => {
      const errors = [
        new ErrorInfo({ message: <Trans i18nKey="errors.caughtError" /> }),
        new ErrorInfo({
          message: <Trans i18nKey="errors.caughtError_NetworkError" />,
        }),
      ];

      renderComponent({ errors });

      expect(screen.getByRole("list")).toMatchInlineSnapshot(`
        <ul
          class="usa-list"
        >
          <li>
            Sorry, an unexpected error in our system was encountered. If this continues to happen, you may call the Paid Family Leave Contact Center at (833) 344‑7365.
          </li>
          <li>
            Sorry, an error was encountered. This may occur for a variety of reasons, including temporarily losing an internet connection or an unexpected error in our system. If this continues to happen, you may call the Paid Family Leave Contact Center at (833) 344‑7365
          </li>
        </ul>
      `);
    });
  });

  describe("when the component mounts", () => {
    it("scrolls to the top of the window when there are errors", () => {
      renderComponent({
        errors: [
          new ErrorInfo({ message: "Mock error message #1" }),
          new ErrorInfo({ message: "Mock error message #2" }),
        ],
      });

      expect(window.scrollTo).toHaveBeenCalledWith(0, 0);
    });

    it("does not scroll if there are no errors", () => {
      renderComponent({ errors: [] });

      expect(global.scrollTo).not.toHaveBeenCalled();
    });
  });

  describe("when the errors change", () => {
    it("scrolls to the top of the window", () => {
      const { rerender } = render(
        <ErrorsSummary
          errors={[
            new ErrorInfo({ message: "Mock error message #1" }),
            new ErrorInfo({ message: "Mock error message #2" }),
          ]}
        />
      );

      rerender(
        <ErrorsSummary errors={[new ErrorInfo({ message: "New error" })]} />
      );
      expect(global.scrollTo).toHaveBeenCalledTimes(2);
      expect(global.scrollTo).toHaveBeenCalledWith(0, 0);
    });
  });

  it("does not render an alert when no errors are null", () => {
    expect(() => {
      renderComponent({ errors: null });
    }).toThrowError();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
