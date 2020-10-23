/** @typedef {import('../models/Document').default} Document */

/**
 * Get only documents associated with a given document_type
 * @param {Document[]} documents
 * @param {string} document_type
 * @returns {Document[]}
 */
const findDocumentsByType = (documents, document_type) => {
  return documents.filter((document) => {
    // Ignore casing differences by comparing lowercased enums
    return document.document_type.toLowerCase() === document_type.toLowerCase();
  });
};

export default findDocumentsByType;
