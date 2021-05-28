import {
  AbstractDocumentGenerator,
  PDFFormData,
} from "./AbstractDocumentGenerator";
import {
  ApplicationRequestBody,
  IntermittentLeavePeriods,
  ReducedScheduleLeavePeriods,
} from "../../api";
import { differenceInWeeks, format, parseISO, subYears } from "date-fns";

export default class HealthCareProviderForm extends AbstractDocumentGenerator<{
  invalid?: boolean;
}> {
  get documentSource(): string {
    return this.path("hcp-v3.pdf");
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
    const conditionStart = subYears(new Date(), 2);
    const data: { [k: string]: string | boolean } = {
      // Employee Info - Section 1
      "Employee name": `${claim.first_name} ${claim.last_name}`,
      Employee: `${claim.first_name} ${claim.last_name}`,
      "Employee first name": `${claim.first_name}`,
      "Employee Last name": `${claim.last_name}`,
      "Emp. DOB mm": format(dob, "MM"),
      "Emp. DOB dd": format(dob, "dd"),
      "Emp. DOB yyyy": config.invalid ? "" : format(dob, "yyyy"),
      "Emp. SSI last 4": `${
        config.invalid ? "" : claim.tax_identifier?.slice(7)
      }`,
      "Are you applying for your own serious health condition?": "Yes",
      "Provider initial Page 3": "TC",

      // Health Condition - Section 2
      "Does the patient have a serious health condition": "Yes",
      "Requires or did require": "On",
      "Requires one medical visit": "On",
      "Condition start mm": format(conditionStart, "MM"),
      "Condition start dd": format(conditionStart, "dd"),
      "Conditiion start yyyy": format(conditionStart, "yyyy"),
      "Provider initial Page 4": "TC",
      "Yes Pregnancy": claim.leave_details?.pregnant_or_recent_birth
        ? "On"
        : false,
      "No pregnancy": claim.leave_details?.pregnant_or_recent_birth
        ? false
        : "On",
      "Is this health condition a jobrelated injury": "No_3",

      // Section 3 #14
      "Continuous leave": claim.has_continuous_leave_periods ? "On" : false,
      "Reduced leave schedule": claim.has_reduced_schedule_leave_periods
        ? "On"
        : false,
      "Intermittent leave": claim.has_intermittent_leave_periods ? "On" : false,
      "Provider initial, Page 5": "TC",
      "Provider initial Page 6": "TC",

      // Practitioner data.
      "Provider name": "Theodore Cure",
      "Provider Title": "MD",
      License: "[assume license is valid]",
      "Area of practice": "General Medicine",
      "Practice name": "[assume business is valid]",
      "Office Phone 1": "555",
      "Office Phone 2": "555",
      "Office phone 3": "5555",
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

        switch (leave_type) {
          case "continuous":
            data["Weeks of continuous leave"] = differenceInWeeks(
              end_date,
              start_date
            ).toString();
            // Leave Period start/end dates
            data["Continuous start mm"] = format(start_date, "MM");
            data["Continuous start dd"] = format(start_date, "dd");
            data["Continuous start yyyy"] = format(start_date, "yyyy");
            data["Continuous end mm"] = format(end_date, "MM");
            data["Continuous end dd"] = format(end_date, "dd");
            data["Continuous end yyyy"] = format(end_date, "yyyy");
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
            data["Intermittent start mm"] = format(start_date, "MM");
            data["Intermittent start dd"] = format(start_date, "dd");
            data["Intermittent start yyyy"] = format(start_date, "yyyy");
            data["Intermittent end mm"] = format(end_date, "MM");
            data["Intermittent end dd"] = format(end_date, "dd");
            data["Intermittent end yyyy"] = format(end_date, "yyyy");
            // Question 21
            data["Absences"] = "Once per week";
            data["Times per week"] = "1";
            // Question 22 - How long will a single absence last? No more than 1 day.
            data["Absence length: At least one day, up to"] = "Less than 1 day";
            // Days it will last.
            data["Days"] = duration.toString();
            data["Yes"] = "Yes";
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
            // Weeks of reduced schedule.
            data["Weeks of a reduced leave schedule"] = differenceInWeeks(
              end_date,
              start_date
            ).toString();
            data["Reduced start mm"] = format(start_date, "MM");
            data["Reduced start dd"] = format(start_date, "dd");
            data["Reduced start yyyy"] = format(start_date, "yyyy");
            data["Reduced end mm"] = format(end_date, "MM");
            data["Reduced end dd"] = format(end_date, "dd");
            data["Reduced end yyyy"] = format(end_date, "yyyy");
            // Hours off.
            data["Hours of reduced leave schedule"] = Math.round(
              totalMinutes / 60
            ).toString();
            break;
        }
      } else {
        switch (leave_type) {
          case "continuous":
            data["No continuous leave needed"] = "On";
            break;
          case "reduced_schedule":
            data["no reduced leave schedule needed"] = "Yes";
            data["No reduced leave schedule needed"] = "On";
            break;
        }
      }
    }
    return data;
  }
}
