import IssueErrorMessage from "src/components/IssueErrorMessage";
import React from "react";
import { initializeI18n } from "src/locales/i18n";
import { render } from "@testing-library/react";

const mockIssueTranslations = {
  fooModel: {
    name: {
      required: "Name is required.",
    },
    rules: {
      minimum: "Foo can't be created this early.",
    },
    conflicting: "Foo already exists",
    intermittent_interval_maximum:
      "<ul><li>Message with a <intermittent-leave-guide>link</a>.</li></ul>",
  },
  validationFallback: {
    required: "{{ field }} is required.",
    invalid: "Field ({{field}}) has invalid value.",
  },
};

async function setTranslations() {
  await initializeI18n("en-US", {
    "en-US": {
      translation: {
        errors: mockIssueTranslations,
      },
    },
  });
}

describe("ErrorMessage", () => {
  beforeAll(async () => {
    await setTranslations();
  });

  it("supports a set of safelisted links and list mark", () => {
    const { container } = render(
      <IssueErrorMessage
        type="intermittent_interval_maximum"
        namespace="fooModel"
      />
    );

    expect(container.innerHTML).toMatchSnapshot();
  });

  it.each([
    [
      // fooModel translation exists for: field+type
      {
        field: "name",
        type: "required",
        message:
          "This fallback message shouldn't render, since there's a matching translation.",
      },
      mockIssueTranslations.fooModel.name.required,
    ],
    [
      // fooModel translation exists for: rule
      {
        field: "name_with_no_translation",
        type: "type_with_no_translation",
        rule: "minimum",
      },
      mockIssueTranslations.fooModel.rules.minimum,
    ],
    [
      // fooModel translation exists for: type
      {
        type: "conflicting",
      },
      mockIssueTranslations.fooModel.conflicting,
    ],
    [
      // validationFallback translation exists for: type
      {
        type: "required",
        field: "unknown_field",
      },
      "unknown_field is required.",
    ],
  ])(
    "renders message based on field+type, rule, and type (in that order)",
    (issue, expectedMessage) => {
      const { container } = render(
        <IssueErrorMessage {...issue} namespace="fooModel" />
      );

      expect(container.innerHTML).toContain(expectedMessage);
    }
  );

  it("falls back to generic field-level message when the field is defined", () => {
    const { container } = render(
      <IssueErrorMessage field="name" namespace="fooModel" />
    );

    expect(container.innerHTML).toContain("Field (name) has invalid value.");
  });

  it("falls back to issue's message when a field isn't defined", () => {
    const { container } = render(
      <IssueErrorMessage message="Foo is invalid." namespace="fooModel" />
    );

    expect(container.innerHTML).toContain("Foo is invalid.");
  });
});
