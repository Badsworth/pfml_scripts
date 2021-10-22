import { render, screen } from "@testing-library/react";
import ErrorBoundary from "../../src/components/ErrorBoundary";
import React from "react";
import userEvent from "@testing-library/user-event";

describe("ErrorBoundary", () => {
  it("renders descendant components when no errors are thrown by descendant component", () => {
    const GoodComponent = () => <div>Hello</div>;

    render(
      <ErrorBoundary>
        <GoodComponent />
      </ErrorBoundary>
    );

    expect(screen.getByText(/Hello/)).toBeInTheDocument();
    expect(screen.queryByRole("region")).not.toBeInTheDocument();
  });

  describe("when an error is thrown by a descendant component", () => {
    const originalLocation = window.location;
    const BadComponent = () => {
      throw new Error("Component broke.");
    };

    beforeEach(() => {
      delete window.location;
      window.location = { reload: jest.fn() };

      // Hide logged errors since that's expected in this scenario
      jest.spyOn(console, "error").mockImplementation(jest.fn());
    });

    afterEach(() => {
      window.location = originalLocation;
      jest.restoreAllMocks();
    });

    it("renders an Alert", () => {
      render(
        <ErrorBoundary>
          <BadComponent />
        </ErrorBoundary>
      );

      expect(() => {
        render(<BadComponent />);
      }).toThrowError();
      expect(screen.getByRole("region")).toMatchSnapshot();
    });

    it("reloads page when reload button is clicked", () => {
      render(
        <ErrorBoundary>
          <BadComponent />
        </ErrorBoundary>
      );

      userEvent.click(screen.getByRole("button"));
      expect(window.location.reload).toHaveBeenCalled();
    });
  });
});
