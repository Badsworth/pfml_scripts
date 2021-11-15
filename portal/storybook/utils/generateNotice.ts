import {
  ClaimDocument,
  DocumentType,
  OtherDocumentType,
} from "src/models/Document";
import { uniqueId } from "lodash";

// Generates notice of type (e.g., denialNotice)
export const generateNotice = (
  type: keyof typeof OtherDocumentType
): ClaimDocument => {
  // Creates random number up to limit {number} value
  const createRandomInteger = (limit: number) => {
    const randomNumber = Math.floor(Math.random() * limit) + 1;
    return `0${randomNumber}`.slice(-2);
  };

  // Four-digit prior year (e.g., 2020)
  const lastYear = new Date().getFullYear() - 1;

  // Random month/day for notice date
  const randomMonth = createRandomInteger(12);
  const randomDay = createRandomInteger(28);

  return {
    created_at: `${lastYear}-${randomMonth}-${randomDay}`,
    document_type: DocumentType[type],
    fineos_document_id: uniqueId("notice"),
    content_type: "application/pdf",
    description: null,
    name: null,
  };
};
