import {
  BenefitsApplicationDocument,
  DocumentType,
  OtherDocumentType,
} from "src/models/Document";
import { uniqueId } from "lodash";

// Generates notice of type (e.g., denialNotice)
export const generateNotice = (
  type: keyof typeof OtherDocumentType,
  customDate?: string
): BenefitsApplicationDocument => {
  // Creates random number up to limit {number} value

  let createdDate = customDate;
  if (!createdDate) {
    const createRandomInteger = (limit: number) => {
      const randomNumber = Math.floor(Math.random() * limit) + 1;
      return `0${randomNumber}`.slice(-2);
    };

    // Four-digit prior year (e.g., 2020)
    const lastYear = new Date().getFullYear() - 1;

    // Random month/day for notice date
    const randomMonth = createRandomInteger(12);
    const randomDay = createRandomInteger(28);
    createdDate = `${lastYear}-${randomMonth}-${randomDay}`;
  }

  return {
    application_id: "mock-application-id",
    created_at: createdDate,
    document_type: DocumentType[type],
    fineos_document_id: uniqueId("notice"),
    content_type: "application/pdf",
    description: "",
    name: "",
    user_id: "",
  };
};
