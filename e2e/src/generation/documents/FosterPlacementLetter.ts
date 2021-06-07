import {
  AbstractDocumentGenerator,
  PDFFormData,
} from "./AbstractDocumentGenerator";
import { ApplicationRequestBody } from "../../api";
import faker from "faker";
import { format, parseISO } from "date-fns";

function reformat(date: string): string {
  return format(parseISO(date), "MM/dd/yyyy");
}

export default class FosterPlacementLetter extends AbstractDocumentGenerator<{
  invalid?: boolean;
}> {
  documentSource(): string {
    return this.path("foster-adopt-cert.pdf");
  }
  getFormData(
    claim: ApplicationRequestBody,
    config: { invalid?: boolean }
  ): PDFFormData {
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
      }
    }
    if (!claim.leave_details?.child_placement_date) {
      throw new Error(
        `Unable to generate foster placement letter without child placement date`
      );
    }
    return {
      "Date Leave to Begin": format(start_date, "MM/dd/yyyy"),
      "Date Leave to End": format(end_date, "MM/dd/yyyy"),
      "Actual or Anticipated Date of Adoption / Placement": reformat(
        claim.leave_details?.child_placement_date
      ),
      "Date Signed": "01/01/2021",
      Fax: "555-555-5555",
      "Signature of Employee": `${claim.first_name} ${claim.last_name}`,
      "Signature of Official": faker.name.findName(),
      "Phone Number": "555-555-1212",
      "Employee Name": config.invalid
        ? faker.name.findName()
        : `${claim.first_name} ${claim.last_name}`,
      Adoption: false,
      "Foster Care Placement": true,
      "Professional / Agency Name and Address": "[assume valid]",
      "Supervisor / Responsible Administrator Name": faker.name.findName(),
      "Employer Name": "[assume this matches claim]",
      "Employer Title": "[assume this matches claim]",
      "Employee's Work Schedule": "[assume this matches claim]",
    };
  }
}
