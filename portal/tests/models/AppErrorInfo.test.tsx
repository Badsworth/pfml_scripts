import { render, screen } from "@testing-library/react";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import React from "react";
import { Trans } from "react-i18next";

describe("AppErrorInfo", () => {
  it("generates a unique key for each instance", () => {
    const errorInfo1 = new AppErrorInfo({ message: "One" });
    const errorInfo2 = new AppErrorInfo({ message: "Two" });

    expect(errorInfo1.key).toEqual(expect.stringContaining("AppErrorInfo"));
    expect(errorInfo2.key).toEqual(expect.stringContaining("AppErrorInfo"));
    expect(errorInfo1.key).not.toEqual(errorInfo2.key);
  });

  describe("fieldErrorMessage", () => {
    const TestErrorComponent = ({ errors }: { errors: React.ReactNode }) => {
      return <div data-testid="error-container">{errors}</div>;
    };

    it("returns null result if there are no errors", () => {
      const result = AppErrorInfo.fieldErrorMessage([], "first_name");

      expect(result).toBeNull();
    });

    it("returns null if no errors match the given field's path", () => {
      const errors = [
        new AppErrorInfo({
          field: "foo",
          message: "Field is required",
        }),
      ];
      const field = "first_name";

      const result = AppErrorInfo.fieldErrorMessage(errors, field);
      render(<TestErrorComponent errors={result} />);
      expect(screen.getByTestId("error-container")).toBeEmptyDOMElement();
    });

    it("returns merged string if multiple errors match the given field's path", () => {
      const field = "birthdate";
      const errors = [
        new AppErrorInfo({
          field,
          message: "Day must be less than 31.",
        }),
        new AppErrorInfo({
          field,
          message: "Year must be greater than 1900.",
        }),
      ];

      const result = AppErrorInfo.fieldErrorMessage(errors, field);
      const { container } = render(<TestErrorComponent errors={result} />);

      expect(container.firstChild).toMatchInlineSnapshot(`
        <div
          data-testid="error-container"
        >
          Day must be less than 31.
           
          Year must be greater than 1900.
        </div>
      `);
    });

    it("returns merged string and components if multiple errors match the given field's path", () => {
      const field = "birthdate";
      const errors = [
        new AppErrorInfo({
          field,
          message: (
            <Trans
              i18nKey="errors.applications.fineos_case_creation_issues"
              components={{
                "mass-gov-form-link": <a href="test/link" />,
              }}
            />
          ),
        }),
        new AppErrorInfo({
          field,
          message: "Fineos issues happened.",
        }),
      ];

      const result = AppErrorInfo.fieldErrorMessage(errors, field);
      const { container } = render(<TestErrorComponent errors={result} />);
      expect(container.firstChild).toMatchInlineSnapshot(`
        <div
          data-testid="error-container"
        >
          We couldn’t find you in our system. Check that you entered your employer’s Employer Identification Number (EIN) correctly. If you continue to get this error, 
          <a
            href="test/link"
          >
            follow these instructions
          </a>
           and we’ll set up your application through our Contact Center.
           
          Fineos issues happened.
        </div>
      `);
    });
  });
});
