import { Issue, ValidationError } from "../../src/errors";
import findErrorMessageForField from "../../src/utils/findErrorMessageForField";
import { render } from "@testing-library/react";

describe("findErrorMessageForField", () => {
  it("returns undefined if there are no errors", () => {
    expect(findErrorMessageForField([], "first_name")).toBeUndefined();
  });

  it("returns undefined if there are no errors associated with the given field", () => {
    const error = new ValidationError(
      [
        {
          field: "last_name",
          type: "required",
        },
      ],
      "applications"
    );
    expect(findErrorMessageForField([error], "first_name")).toBeUndefined();
  });

  it("returns an error message when an error is associated with the given field", () => {
    const error = new ValidationError(
      [
        {
          field: "first_name",
          type: "required",
        },
      ],
      "applications"
    );

    const Message = findErrorMessageForField([error], "first_name");
    const { container } = render(Message as JSX.Element);

    expect(container.innerHTML).toMatchInlineSnapshot(`"Enter a first name."`);
  });

  it("supports any error type with an issues property", () => {
    class TestError extends Error {
      issues: Issue[];
      i18nPrefix: string;

      constructor() {
        super();
        this.issues = [
          {
            field: "first_name",
            type: "required",
          },
        ];

        this.i18nPrefix = "applications";
      }
    }

    const Message = findErrorMessageForField([new TestError()], "first_name");
    const { container } = render(Message as JSX.Element);

    expect(container.innerHTML).toMatchInlineSnapshot(`"Enter a first name."`);
  });
});
