import {
  BenefitsApplicationDocument,
  ClaimDocument,
  DocumentTypeEnum,
} from "../models/Document";

/**
 * Get only documents associated with a given selection of document_types
 */
function findDocumentsByTypes<
  T extends BenefitsApplicationDocument | ClaimDocument
>(documents: T[], document_types: DocumentTypeEnum[]): T[] {
  const lowerCaseDocumentTypes = document_types.map((documentType) =>
    documentType.toLowerCase()
  );

  return documents.filter((document) => {
    // Ignore casing differences by comparing lowercased enums
    return lowerCaseDocumentTypes.includes(
      document.document_type.toLowerCase()
    );
  });
}

export default findDocumentsByTypes;
