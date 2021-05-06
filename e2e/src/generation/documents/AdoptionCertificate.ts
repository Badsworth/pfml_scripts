import {
  AbstractDocumentGenerator,
  DocumentType,
  PDFFormData,
} from "./AbstractDocumentGenerator";
import { ApplicationRequestBody } from "../../api";
import faker from "faker";
import { format, parseISO } from "date-fns";

function reformat(date: string): string {
  return format(parseISO(date), "MM/dd/yyyy");
}

export default class AdoptionCertificate extends AbstractDocumentGenerator<{
  invalid?: boolean;
}> {
  get documentType(): DocumentType {
    return "Child bonding evidence form";
  }
  get documentSource(): string {
    return this.path("foster-adopt-cert.pdf");
  }
  getFormData(
    claim: ApplicationRequestBody,
    config: { invalid?: boolean }
  ): PDFFormData {
    if (
      !claim.leave_details?.continuous_leave_periods?.[0].start_date ||
      !claim.leave_details?.continuous_leave_periods?.[0].end_date
    ) {
      throw new Error(
        "Invalid leave period to generate foster placement letter"
      );
    }
    if (!claim.leave_details?.child_placement_date) {
      throw new Error(
        `Unable to generate foster placement letter without child placement date`
      );
    }
    return {
      "Date Leave to Begin": reformat(
        claim.leave_details?.continuous_leave_periods[0].start_date
      ),
      "Date Leave to End": reformat(
        claim.leave_details?.continuous_leave_periods[0].end_date
      ),
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
      Adoption: true,
      "Foster Care Placement": false,
      "Professional / Agency Name and Address": "[assume valid]",
      "Supervisor / Responsible Administrator Name": faker.name.findName(),
      "Employer Name": "[assume this matches claim]",
      "Employer Title": "[assume this matches claim]",
      "Employee's Work Schedule": "[assume this matches claim]",
    };
  }
}
