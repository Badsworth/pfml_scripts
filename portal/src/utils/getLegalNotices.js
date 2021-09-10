import { DocumentType } from "../models/Document";
import findDocumentsByTypes from "./findDocumentsByTypes";

/** @typedef {import('../models/Document').default} Document */

/**
 * Get only documents that are legal notices.
 * @param {Document[]} documents
 * @returns {Document[]}
 */
const getLegalNotices = (documents) => {
  return findDocumentsByTypes(documents, [
    DocumentType.appealAcknowledgement,
    DocumentType.approvalNotice,
    DocumentType.denialNotice,
    DocumentType.requestForInfoNotice,
    DocumentType.withdrawalNotice,
  ]);
};

export default getLegalNotices;
