/** @typedef {import('../models/Document').default} Document */

/**
 * Get only documents associated with a given document_type
 * @param {Document[]} documents
 * @param {string} document_type
 * @returns {Document[]}
 */
const findDocumentsByType = (documents, document_type) => {
  return documents.filter((document) => {
    return document.document_type === document_type;
  });
};

export default findDocumentsByType;
