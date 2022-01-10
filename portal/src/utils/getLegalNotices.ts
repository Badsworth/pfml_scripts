import {
  BenefitsApplicationDocument,
  ClaimDocument,
  DocumentType,
} from "../models/Document";

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
    DocumentType.maximumWeeklyBenefitChangeNotice,
    DocumentType.benefitAmountChangeNotice,
    DocumentType.leaveAllotmentChangeNotice,
    DocumentType.approvedTimeCancelled,
    DocumentType.changeRequestApproved,
    DocumentType.changeRequestDenied,
  ]);
};

export default getLegalNotices;
