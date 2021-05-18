import {
  AbstractDocumentGenerator,
  PDFFormData,
} from "./AbstractDocumentGenerator";
import {
  ApplicationRequestBody,
  IntermittentLeavePeriods,
  ReducedScheduleLeavePeriods,
} from "../../api";
import { differenceInWeeks, format, parseISO } from "date-fns";

export default class HealthCareProviderForm extends AbstractDocumentGenerator<{
  invalid?: boolean;
}> {
  get documentSource(): string {
    return this.path("hcp-real.pdf");
  }
  getFormData(
    claim: ApplicationRequestBody,
    config: { invalid?: boolean }
  ): PDFFormData {
    if (!claim.first_name || !claim.last_name || !claim.date_of_birth) {
      throw new Error("Unable to generate document due to missing properties");
    }
    // Note: To debug this PDF's fields, follow this: https://stackoverflow.com/a/38257183
    const dob = parseISO(claim.date_of_birth);
    const data: { [k: string]: string | boolean } = {
      untitled1: `${claim.first_name} ${claim.last_name}`,
      untitled46: `${claim.first_name} ${claim.last_name}`,
      untitled47: `${claim.first_name} ${claim.last_name}`,
      untitled48: `${claim.first_name} ${claim.last_name}`,
      untitled50: `${claim.first_name} ${claim.last_name}`,
      untitled4: format(dob, "MM"),
      untitled5: format(dob, "dd"),
      untitled6: config.invalid ? "" : format(dob, "yyyy"),
      untitled3: `${config.invalid ? "" : claim.tax_identifier?.slice(7)}`,
      // Checkbox 5 - "I am taking leave because of my own serious health condition"
      untitled51: "Yes",
      // Checkbox 12 - "Does the patient have a serious health condition that necessitates continuing care􏰗"
      untitled56: "Yes",
      // Checkbox 13 - "When did the condition begin􏰗"
      untitled59: "Yes",
      // Checkbox 14 - "Which of the following characteristics apply..."
      untitled60: "Yes",
      // Checkbox 15 - "Is the patient􏰑s serious health condition a pregnancy􏰖related issue"
      untitled65: "Yes",
      // Checkbox 16 - "Is this health condition a work􏰖related injury􏰗"
      untitled67: "Yes",
      // Checkbox 17 - "Is this health condition related to the patient􏰑s military service􏰗"
      untitled69: "Yes",
      // Checkbox 19 - Leave Type? Continuous
      untitled72: claim.has_continuous_leave_periods ? "Yes" : false,
      // Checkbox 19 - Leave Type? Reduced
      untitled73: claim.has_reduced_schedule_leave_periods ? "Yes" : false,
      // Checkbox 19 - Leave Type? Intermittent
      untitled74: claim.has_intermittent_leave_periods ? "Yes" : false,
      // Checkbox 22 - What level of physical exertion - very heavy
      untitled79: "Yes",
      // Checkbox 23 - Is your medical opinion that...
      untitled80: "Yes",
      // Checkbox 24 - "During this time􏰐 are there any other potentially work􏰖related activities" - Yes
      untitled82: "Yes",
      // Text 25 - What to refrain from:
      untitled29: "All work",

      // Checkbox 27 - Reduced leave? No
      untitled87: "Yes",

      // Practitioner data.
      untitled39: "Theodore Cure, MD",
      untitled40: "[assume license is valid]",
      untitled41: "General Medicine",
      untitled42: "[assume business is valid]",
      untitled44: "555-555-5555",
      untitled45: "example@example.com",
    };
    let start_date = new Date();
    let end_date = new Date();

    const leave_types = ["continuous", "reduced_schedule", "intermittent"];
    for (const leave_type of leave_types) {
      const flagKey = `has_${leave_type}_leave_periods` as keyof typeof claim;
      const leaveKey = `${leave_type}_leave_periods` as
        | "continuous_leave_periods"
        | "reduced_schedule_leave_periods"
        | "intermittent_leave_periods";
      if (claim[flagKey]) {
        const period = (claim.leave_details?.[leaveKey] ?? [])[0];
        if (!period) {
          throw new Error(`No ${leave_type} periods found on this claim`);
        }
        if (!period.start_date || !period.end_date) {
          throw new Error(`Leave period does not have a start or end date`);
        }
        start_date = parseISO(period.start_date);
        end_date = parseISO(period.end_date);

        data["untitled21"] = format(start_date, "MM");
        data["untitled22"] = format(start_date, "dd");
        data["untitled23"] = format(start_date, "yyyy");
        data["untitled24"] = format(end_date, "MM");
        data["untitled25"] = format(end_date, "dd");
        data["untitled26"] = format(end_date, "yyyy");

        switch (leave_type) {
          case "continuous":
            // Checkbox 26  - Continuous Leave? Yes
            data["untitled84"] = true;
            data["untitled31"] = differenceInWeeks(
              end_date,
              start_date
            ).toString();
            break;
          case "intermittent":
            const {
              duration,
              duration_basis,
              frequency_interval_basis,
              frequency,
            } = period as IntermittentLeavePeriods;
            if (frequency_interval_basis !== "Weeks" && frequency !== 1) {
              throw new Error(
                "Unable to handle intermittent leave frequencies of anything other than 1 week."
              );
            }
            if (duration_basis !== "Days" || !duration) {
              throw new Error(
                "Unable to handle intermittent leave durations of anything other than 1 days."
              );
            }
            // Checkbox 29 - Intermittent leave periods:
            data["untitled89"] = true;
            data["untitled34"] = "1";
            // Checkbox 30 - How long will a single absence last? No more than 1 day.
            data["untitled93"] = true;
            // Days it will last.
            data["untitled38"] = duration.toString();
            break;
          case "reduced_schedule":
            const reducedPeriod = period as ReducedScheduleLeavePeriods;
            const totalMinutes =
              (reducedPeriod.monday_off_minutes ?? 0) +
              (reducedPeriod.tuesday_off_minutes ?? 0) +
              (reducedPeriod.wednesday_off_minutes ?? 0) +
              (reducedPeriod.thursday_off_minutes ?? 0) +
              (reducedPeriod.friday_off_minutes ?? 0) +
              (reducedPeriod.saturday_off_minutes ?? 0) +
              (reducedPeriod.sunday_off_minutes ?? 0);
            data["untitled86"] = true;
            // Weeks of reduced schedule.
            data["untitled32"] = differenceInWeeks(
              end_date,
              start_date
            ).toString();
            // Hours off.
            data["untitled33"] = Math.round(totalMinutes / 60).toString();
            break;
        }
      } else {
        switch (leave_type) {
          case "continuous":
            // Checkbox 26 Continuous leave? No.
            data["untitled85"] = true;
            break;
          case "intermittent":
            // Intermittent leave? No.
            data["untitled88"] = true;
            break;
          case "reduced_schedule":
            // Reduced leave? No
            data["untitled87"] = true;
            break;
        }
      }
    }
    return data;
  }
}
