import { NetworkError, ValidationError } from "src/errors";
import { render, screen } from "@testing-library/react";
import ErrorMessage from "src/components/ErrorMessage";
import React from "react";

describe("ErrorMessage", () => {
  it("renders listing of each issues entry when present on the error", () => {
    const error = new ValidationError([
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
    ]);
    render(<ErrorMessage error={error} />);

    expect(screen.getByRole("list")).toMatchSnapshot();
  });

  it("does not render a list when there's only one issues entry", () => {
    const error = new ValidationError([
      {
        field: "first_name",
        type: "required",
        namespace: "applications",
      },
    ]);
    render(<ErrorMessage error={error} />);

    expect(screen.queryByRole("list")).not.toBeInTheDocument();
    expect(screen.getByText(/Enter a first name/)).toBeInTheDocument();
  });

  it("renders message based on the error's name when the error has no issues property", () => {
    const error = new NetworkError("Network error");
    const { container } = render(<ErrorMessage error={error} />);
    expect(container).toHaveTextContent(/losing an internet connection/);
  });

  it("renders generic message when the error has an empty issues property", () => {
    const error = {
      name: "TestError",
      issues: [],
      message: "This is a test error",
    };

    const { container } = render(<ErrorMessage error={error} />);
    expect(container).toHaveTextContent(/unexpected error/);
  });

  it("falls back to generic error message when an i18n key doesn't exist for the error type", () => {
    const error = new Error("JS error");
    const { container } = render(<ErrorMessage error={error} />);
    expect(container).toHaveTextContent(
      /unexpected error in our system was encountered/
    );
  });
});
