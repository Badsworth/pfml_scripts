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
        namespace: "applications",
      },
      {
        type: "conflicting",
        rule: "disallow_hybrid_intermittent_leave",
        message:
          "Intermittent leave cannot be taken alongside Continuous or Reduced Schedule leave",
        namespace: "applications",
      },
    ];
    const missingFields = getMissingRequiredFields([
      new ValidationError(issues),
    ]);
    expect(missingFields).toEqual([]);
  });

  it("returns only the required field errors if there are multiple errors", () => {
    const issues = [
      {
        type: "checksum",
        field: "application.payment_preferences.routing_number",
        message: "Routing number is invalid",
        namespace: "applications",
      },
      {
        type: "required",
        field: "application.has_other_incomes",
        namespace: "applications",
      },
      {
        type: "conflicting",
        rule: "disallow_hybrid_intermittent_leave",
        message:
          "Intermittent leave cannot be taken alongside Continuous or Reduced Schedule leave",
        namespace: "applications",
      },
      {
        type: "required",
        field: "application.has_employer_benefits",
        namespace: "applications",
      },
    ];
    const missingFields = getMissingRequiredFields([
      new ValidationError(issues),
    ]);
    expect(missingFields).toEqual([
      {
        type: "required",
        field: "application.has_other_incomes",
        namespace: "applications",
      },
      {
        type: "required",
        field: "application.has_employer_benefits",
        namespace: "applications",
      },
    ]);
  });

  it("returns only the basic required field errors if there are multiple errors", () => {
    const issues = [
      {
        type: "checksum",
        field: "application.payment_preferences.routing_number",
        message: "Routing number is invalid",
        namespace: "applications",
      },
      {
        type: "required",
        field: "application.has_other_incomes",
        namespace: "applications",
      },
      {
        type: "conflicting",
        rule: "disallow_hybrid_intermittent_leave",
        message:
          "Intermittent leave cannot be taken alongside Continuous or Reduced Schedule leave",
        namespace: "applications",
      },
      {
        type: "required",
        field: "application.has_employer_benefits",
        namespace: "applications",
      },
      {
        type: "required",
        rule: "require_employer_notified",
        message: "you must notify your employer",
        namespace: "applications",
      },
    ];
    const missingFields = getMissingRequiredFields([
      new ValidationError(issues),
    ]);
    expect(missingFields).toEqual([
      {
        type: "required",
        field: "application.has_other_incomes",
        namespace: "applications",
      },
      {
        type: "required",
        field: "application.has_employer_benefits",
        namespace: "applications",
      },
    ]);
  });
});
