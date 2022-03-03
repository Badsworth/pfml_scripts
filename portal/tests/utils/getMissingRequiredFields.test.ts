import { NetworkError, ValidationError } from "../../src/errors";
import getMissingRequiredFields from "../../src/utils/getMissingRequiredFields";

describe("getMissingRequiredFields", () => {
  it("returns empty array if there are no errors", () => {
    const missingFields = getMissingRequiredFields([]);
    expect(missingFields).toEqual([]);
  });

  it("returns empty array if there are no errors with issues", () => {
    const missingFields = getMissingRequiredFields([new NetworkError()]);
    expect(missingFields).toEqual([]);
  });

  it("returns empty array if there are no required field errors", () => {
    const issues = [
      {
        type: "checksum",
        field: "application.payment_preferences.routing_number",
        message: "Routing number is invalid",
      },
      {
        type: "conflicting",
        rule: "disallow_hybrid_intermittent_leave",
        message:
          "Intermittent leave cannot be taken alongside Continuous or Reduced Schedule leave",
      },
    ];
    const missingFields = getMissingRequiredFields([
      new ValidationError(issues, "applications"),
    ]);
    expect(missingFields).toEqual([]);
  });

  it("returns only the required field errors if there are multiple errors", () => {
    const issues = [
      {
        type: "checksum",
        field: "application.payment_preferences.routing_number",
        message: "Routing number is invalid",
      },
      {
        type: "required",
        field: "application.has_other_incomes",
      },
      {
        type: "conflicting",
        rule: "disallow_hybrid_intermittent_leave",
        message:
          "Intermittent leave cannot be taken alongside Continuous or Reduced Schedule leave",
      },
      {
        type: "required",
        field: "application.has_employer_benefits",
      },
    ];
    const missingFields = getMissingRequiredFields([
      new ValidationError(issues, "applications"),
    ]);
    expect(missingFields).toEqual([
      {
        type: "required",
        field: "application.has_other_incomes",
      },
      {
        type: "required",
        field: "application.has_employer_benefits",
      },
    ]);
  });

  it("returns only the basic required field errors if there are multiple errors", () => {
    const issues = [
      {
        type: "checksum",
        field: "application.payment_preferences.routing_number",
        message: "Routing number is invalid",
      },
      {
        type: "required",
        field: "application.has_other_incomes",
      },
      {
        type: "conflicting",
        rule: "disallow_hybrid_intermittent_leave",
        message:
          "Intermittent leave cannot be taken alongside Continuous or Reduced Schedule leave",
      },
      {
        type: "required",
        field: "application.has_employer_benefits",
      },
      {
        type: "required",
        rule: "require_employer_notified",
        message: "you must notify your employer",
      },
    ];
    const missingFields = getMissingRequiredFields([
      new ValidationError(issues, "applications"),
    ]);
    expect(missingFields).toEqual([
      {
        type: "required",
        field: "application.has_other_incomes",
      },
      {
        type: "required",
        field: "application.has_employer_benefits",
      },
    ]);
  });
});
