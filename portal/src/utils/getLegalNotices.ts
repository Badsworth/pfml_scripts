import BenefitsApplicationDocument from "../models/BenefitsApplicationDocument";
import ClaimDocument from "../models/ClaimDocument";
import { DocumentType } from "../models/Document";
import findDocumentsByTypes from "./findDocumentsByTypes";

/**
 * Get only documents that are legal notices.
 */
const getLegalNotices = (
  documents: Array<BenefitsApplicationDocument | ClaimDocument>
) => {
  return findDocumentsByTypes(documents, [
    DocumentType.appealAcknowledgment,
    DocumentType.approvalNotice,
    DocumentType.denialNotice,
    DocumentType.requestForInfoNotice,
    DocumentType.withdrawalNotice,
  ]);
};

export default getLegalNotices;
