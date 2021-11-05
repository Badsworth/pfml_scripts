import { DocumentType } from "src/models/Document";
import { uniqueId } from "lodash";

// Generates notice of type (e.g., denialNotice)
// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'type' implicitly has an 'any' type.
export const generateNotice = (type) => {
  // Creates random number up to limit {number} value
  // @ts-expect-error ts-migrate(7006) FIXME: Parameter 'limit' implicitly has an 'any' type.
  const createRandomInteger = (limit) => {
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
    // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
    document_type: DocumentType[type],
    fineos_document_id: uniqueId("notice"),
  };
};
