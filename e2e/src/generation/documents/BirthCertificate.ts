import {
  AbstractDocumentGenerator,
  DocumentType,
  PDFFormData,
} from "./AbstractDocumentGenerator";
import { ApplicationRequestBody } from "../../api";
import faker from "faker";
import { format, parseISO } from "date-fns";

export default class BirthCertificate extends AbstractDocumentGenerator<{
  invalid?: boolean;
}> {
  get documentType(): DocumentType {
    return "Child bonding evidence form";
  }
  get documentSource(): string {
    return this.path("birth-certificate.pdf");
  }
  getFormData(
    claim: ApplicationRequestBody,
    config: { invalid?: boolean }
  ): PDFFormData {
    if (!claim.leave_details?.child_birth_date) {
      throw new Error(
        `No birth date was given. Unable to generate birth certificate.`
      );
    }
    if (!claim.first_name || !claim.last_name) {
      throw new Error("Claim is missing required properties");
    }
    const gender = faker.random.number(1);
    const race = faker.random.arrayElement([
      "White",
      "Asian",
      "Black or African American",
      "Hispanic or Latino",
    ]);
    const dob = format(
      parseISO(claim.leave_details.child_birth_date),
      "MM/dd/yyyy"
    );

    const employee = {
      first_name: claim.first_name,
      last_name: claim.last_name,
    };
    if (config.invalid) {
      employee.first_name = faker.name.firstName(gender);
      employee.last_name = faker.name.lastName(gender);
    }
    const employeeName = `${employee.first_name} ${employee.last_name}`;
    const spouseName = faker.name.findName(undefined, employee.last_name, 0);
    const childName = faker.name.findName(
      undefined,
      employee.last_name,
      gender
    );
    return {
      "Certificate Number": "123",
      "Record Number": "123",
      "Date of Birth": dob,
      "Name of Child": childName,
      Sex: gender === 0 ? "Male" : "Female",
      Race: race,
      "Name of Mother": employeeName,
      "Name of Father": spouseName,
      "Birthplace of Mother": faker.fake("{{address.city}}, {{address.state}}"),
      "Birthplace of Father": faker.fake("{{address.city}}, {{address.state}}"),
      "Place of Birth": faker.fake("{{address.city}}, {{address.state}}"),
      "Residence of Parents": faker.fake("{{address.city}}, {{address.state}}"),
      "Occupation of Parent": "Widget Maker",
      "Date of Record": dob,
      "Name of Informant": faker.fake("{{name.firstName}} {{name.lastName}}"),
      "Address of Informant": faker.fake("{{address.city}}, {{address.state}}"),
      "Witness Date": dob,
    };
  }
}
