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
import faker from "faker";

export default class CaringLeaveProviderForm extends AbstractDocumentGenerator<{
  invalid?: boolean;
}> {
  documentSource(): string {
    return this.path("caring-v1.1.2.pdf");
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
    const familyMemberDOB = parseISO(
      claim.leave_details?.caring_leave_metadata
        ?.family_member_date_of_birth as string
    );
    const conditionStart = subYears(new Date(), 2);
    const data: { [k: string]: string | boolean } = {
      // Employee Info - Section 1
      "Employee Name": `${claim.first_name} ${claim.last_name}`, // employee at top of pages
      "Employee name": `${claim.first_name} ${claim.last_name}`, // employee at top of page (different FN)
      "Employee first name": `${claim.first_name}`,
      "Employee Last name": `${claim.last_name}`,
      "Emp. DOB mm": format(dob, "MM"),
      "Emp. DOB dd": format(dob, "dd"),
      "Emp. DOB yyyy": config.invalid ? "" : format(dob, "yyyy"),
      "Emp. SSI last 4": `${
        config.invalid ? "" : claim.tax_identifier?.slice(7)
      }`,
      "Why are you applying for leave?":
        "To care for a family member with a serious health condition",

      // Family member information - Section 2
      "The family member who is experiencing a serious health condition is my:":
        "Sibling",
      "Family member name: First": claim.leave_details?.caring_leave_metadata
        ?.family_member_first_name as string,
      "Family member name: Last": claim.leave_details?.caring_leave_metadata
        ?.family_member_last_name as string,
      "Family member address: Street:": faker.address.streetAddress(),
      "Family member address: City:": faker.address.city(),
      "Family member address: State:": faker.address.stateAbbr(),
      "Family member address: Zipcode:": faker.address.zipCode("#####"),
      "Family member address: Country:": "United States",
      "Family member's date of birth: MM": format(familyMemberDOB, "MM"),
      "Family member's date of birth: DD": format(familyMemberDOB, "dd"),
      "Family member's date of birth: yyyy": format(familyMemberDOB, "yyyy"),
      "Employee signature date: MM": format(new Date(), "MM"),
      "Employee signature date: DD": format(new Date(), "dd"),
      "Employee signature date: yyyy": format(new Date(), "yyyy"),

      // Health Condition - Section 3
      // "Does the family member (your patient) have a serious health condition": "Yes",
      // "Does the family member have serious health condition": "Yes",
      "Does the family member (your patient) have a serious health condition as defined by the criteria on page 2?":
        "Yes",
      "Requires, or did require inpatient care": "Yes",
      "Requires one medical visit, plus a regimen of care": "Yes",
      "Condition start mm": format(conditionStart, "MM"),
      "Condition start dd": format(conditionStart, "dd"),
      "Conditiion start yyyy": format(conditionStart, "yyyy"),
      "Is this health condition related to the patient's military service?":
        "No",
      "Medical facts": "Patient has limited mobility and needs assistance.",
      "Describe the kinds of care related to the patient's condition that the employee will provide":
        "Patient has limited mobility and needs assistance.",
      "Will the employee be required to take leave to care for the patient?":
        "Yes",

      // Estimate Leave Details - Section 4
      "Continuous leave": claim.has_continuous_leave_periods ? "On" : false,
      "Reduced leave schedule": claim.has_reduced_schedule_leave_periods
        ? "On"
        : false,
      "Intermittent leave": claim.has_intermittent_leave_periods ? "On" : false,

      // Practitioner data.
      "Provider name": "Theodore Cure",
      "Provider Title": "MD",
      License: "[assume license is valid]",
      "Area of practice": "General Medicine",
      "Practice name": "[assume business is valid]",
      "Office Phone 1": "555",
      "Office Phone 2": "555",
      "Office phone 3": "5555",
      // On multiple pages
      "Healthcare Provider Initials": "TC",
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
            // Section 4A
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
            // Section 4C
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
            // Question 28
            data["Absences"] = "Once per week";
            data["Times per week"] = "1";
            // Question 29 - How long will a single absence last? No more than 1 day.
            data["Absence length: At least one day, up to"] = "Less than 1 day";
            // Days it will last.
            data["Days"] = duration.toString();
            break;
          case "reduced_schedule":
            // Section 4B
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
          case "intermittent":
            data["Absence length"] = "N/A";
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
