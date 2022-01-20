import AppErrorInfo from "../../src/models/AppErrorInfo";
import getMissingRequiredFields from "../../src/utils/getMissingRequiredFields";

describe("getMissingRequiredFields", () => {
  it("returns empty array if there are no errors", () => {
    const missingFields = getMissingRequiredFields([]);
    expect(missingFields).toEqual([]);
  });

  it("returns empty array if there are no required field errors", () => {
    const errors = [
      new AppErrorInfo({
        type: "checksum",
        field: "application.payment_preferences.routing_number",
        message: "Routing number is invalid",
      }),
      new AppErrorInfo({
        type: "conflicting",
        rule: "disallow_hybrid_intermittent_leave",
        message:
          "Intermittent leave cannot be taken alongside Continuous or Reduced Schedule leave",
      }),
    ];
    const missingFields = getMissingRequiredFields(errors);
    expect(missingFields).toEqual([]);
  });

  it("returns only the required field errors if there are multiple errors", () => {
    const errors = [
      new AppErrorInfo({
        type: "checksum",
        field: "application.payment_preferences.routing_number",
        message: "Routing number is invalid",
      }),
      new AppErrorInfo({
        type: "required",
        field: "application.has_other_incomes",
      }),
      new AppErrorInfo({
        type: "conflicting",
        rule: "disallow_hybrid_intermittent_leave",
        message:
          "Intermittent leave cannot be taken alongside Continuous or Reduced Schedule leave",
      }),
      new AppErrorInfo({
        type: "required",
        field: "application.has_employer_benefits",
      }),
    ];
    const missingFields = getMissingRequiredFields(errors);
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
    const errors = [
      new AppErrorInfo({
        type: "checksum",
        field: "application.payment_preferences.routing_number",
        message: "Routing number is invalid",
      }),
      new AppErrorInfo({
        type: "required",
        field: "application.has_other_incomes",
      }),
      new AppErrorInfo({
        type: "conflicting",
        rule: "disallow_hybrid_intermittent_leave",
        message:
          "Intermittent leave cannot be taken alongside Continuous or Reduced Schedule leave",
      }),
      new AppErrorInfo({
        type: "required",
        field: "application.has_employer_benefits",
      }),
      new AppErrorInfo({
        type: "required",
        rule: "require_employer_notified",
        message: "you must notify your employer",
      }),
    ];
    const missingFields = getMissingRequiredFields(errors);
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
