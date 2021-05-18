import {
  AbstractDocumentGenerator,
  PDFFormData,
} from "./AbstractDocumentGenerator";
import { ApplicationRequestBody } from "../../api";
import { format, parseISO } from "date-fns";

export default class PersonalLetter extends AbstractDocumentGenerator<{
  birthDate?: string;
}> {
  get documentSource(): string {
    return this.path("personal-letter.pdf");
  }
  getFormData(
    claim: ApplicationRequestBody,
    config: { birthDate?: string }
  ): PDFFormData {
    if (!claim.leave_details?.child_birth_date) {
      throw new Error(
        "Claim missing required properties to generate a pre-birth letter"
      );
    }
    const dob = config.birthDate
      ? parseISO(config.birthDate)
      : parseISO(claim.leave_details?.child_birth_date);
    return {
      Date: "01/01/2021",
      "Name of Signee": "Robert Uncleman",
      Relationship: "Uncle",
      "Name of Parent(s)": `${claim.first_name} ${claim.last_name}`,
      "Due Date": format(dob, "MM/dd/yyyy"),
    };
  }
}
