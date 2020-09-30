const findDocumentsByType = (documents, documentType) => {
  return documents.filter((document) => {
    return document.document_type === documentType;
  });
};

export default findDocumentsByType;
