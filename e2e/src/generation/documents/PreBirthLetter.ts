import {
  AbstractDocumentGenerator,
  PDFFormData,
} from "./AbstractDocumentGenerator";
import { ApplicationRequestBody } from "../../api";
import { format, parseISO } from "date-fns";
import faker from "faker";

export default class PrebirthLetter extends AbstractDocumentGenerator<{
  birthDate?: string;
}> {
  documentSource(): string {
    return this.path("pre-birth-letter.pdf");
  }
  getFormData(
    claim: ApplicationRequestBody,
    config: { birthDate?: string }
  ): PDFFormData {
    if (!claim.last_name || !claim.leave_details?.child_birth_date) {
      throw new Error(
        "Claim missing required properties to generate a pre-birth letter"
      );
    }
    const dob = config.birthDate
      ? parseISO(config.birthDate)
      : parseISO(claim.leave_details?.child_birth_date);
    return {
      Date: "01/01/2021",
      "Name of Doctor": "Theodore T. Cure",
      "Name of Practice": "Cure Cares",
      "Name of Child(ren)": `${faker.name.firstName()} ${claim.last_name}`,
      "Name of Parent(s)": `${claim.first_name} ${claim.last_name}`,
      "Due Date": format(dob, "MM/dd/yyyy"),
    };
  }
}
