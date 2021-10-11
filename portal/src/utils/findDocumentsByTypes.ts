/** @typedef {import('../models/Document').default} Document */

/**
 * Get only documents associated with a given selection of document_types
 * @param {Document[]} documents
 * @param {string[]} document_types
 * @returns {Document[]}
 */
const findDocumentsByTypes = (documents, document_types) => {
  const lowerCaseDocumentTypes = document_types.map((documentType) =>
    documentType.toLowerCase()
  );
  return documents.filter((document) => {
    // Ignore casing differences by comparing lowercased enums
    return lowerCaseDocumentTypes.includes(
      document.document_type.toLowerCase()
    );
  });
};

export default findDocumentsByTypes;
