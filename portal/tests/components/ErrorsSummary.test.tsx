import {
  InternalServerError,
  NetworkError,
  ValidationError,
} from "../../src/errors";
import { render, screen } from "@testing-library/react";
import ErrorsSummary from "../../src/components/ErrorsSummary";
import React from "react";

describe("ErrorsSummary", () => {
  it("does not render an alert when no errors exist", () => {
    render(<ErrorsSummary errors={[]} />);

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("renders the singular heading and error message when only one error exists", () => {
    render(<ErrorsSummary errors={[new InternalServerError()]} />);

    expect(
      screen.getByRole("heading", {
        name: /An error occurred/,
      })
    ).toBeInTheDocument();
    expect(
      screen.getByText(/an unexpected error in our system was encountered/)
    ).toBeInTheDocument();
  });

  it("renders the singular heading when all errors are of the same type", () => {
    render(
      <ErrorsSummary
        errors={[new InternalServerError(), new InternalServerError()]}
      />
    );

    expect(
      screen.getByRole("heading", {
        name: /An error occurred/,
      })
    ).toBeInTheDocument();
  });

  it("renders the plural heading and list of error messages when more than one error exists", () => {
    render(
      <ErrorsSummary
        errors={[
          new ValidationError([
            {
              field: "first_name",
              type: "required",
              namespace: "applications",
            },
            {
              field: "last_name",
              type: "required",
              namespace: "applications",
            },
          ]),
        ]}
      />
    );

    expect(
      screen.getByRole("heading", {
        name: /2 errors occurred/,
      })
    ).toBeInTheDocument();
    expect(screen.queryAllByRole("listitem")).toHaveLength(2);
  });

  it("scrolls to the top of the window when there are errors", () => {
    render(<ErrorsSummary errors={[new InternalServerError()]} />);

    expect(window.scrollTo).toHaveBeenCalledWith(0, 0);
  });

  it("does not scroll if there are no errors", () => {
    render(<ErrorsSummary errors={[]} />);

    expect(global.scrollTo).not.toHaveBeenCalled();
  });

  it("scrolls to the top of the window when the errors change", () => {
    const { rerender } = render(
      <ErrorsSummary errors={[new InternalServerError()]} />
    );

    rerender(<ErrorsSummary errors={[new NetworkError()]} />);
    expect(global.scrollTo).toHaveBeenCalledTimes(2);
    expect(global.scrollTo).toHaveBeenCalledWith(0, 0);
  });
});
