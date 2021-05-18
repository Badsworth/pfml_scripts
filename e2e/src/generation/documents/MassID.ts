import { ApplicationRequestBody } from "../../api";
import { format, parseISO } from "date-fns";
import {
  AbstractDocumentGenerator,
  PDFFormData,
} from "./AbstractDocumentGenerator";
import { EmployeeGenerator } from "../Employee";

export default class MassID extends AbstractDocumentGenerator<{
  invalid?: boolean;
}> {
  get documentSource(): string {
    return this.path(`license-MA.pdf`);
  }
  getFormData(
    claim: ApplicationRequestBody,
    config: { invalid?: boolean }
  ): PDFFormData {
    if (!claim.first_name || !claim.last_name || !claim.date_of_birth) {
      throw new Error("Unable to generate document due to missing properties");
    }
    const dob = format(parseISO(claim.date_of_birth), "MM/dd/yyyy");
    return {
      "Name first": claim.first_name,
      "Name last": claim.last_name,
      "Date birth": dob,
      "License number": claim.mass_id ?? EmployeeGenerator.generateMassId(),
      "Date issue": "01/01/2016",
      "Date expiration": config.invalid ? "01/01/2020" : "01/01/2028",
      "Address street": claim.mailing_address?.line_1 ?? "",
      "Address state": claim.mailing_address?.state ?? "",
      "Address city": claim.mailing_address?.city ?? "",
      "address ZIP": claim.mailing_address?.zip ?? "",
    };
  }
}
