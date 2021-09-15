import Document, { DocumentType } from "../../src/models/Document";

import LeaveReason from "../../src/models/LeaveReason";
import getLegalNotices from "../../src/utils/getLegalNotices";

describe("getLegalNotices", () => {
  it("filters out all non-legal notices", () => {
    const legalNoticeTypes = new Set([
      DocumentType.appealAcknowledgment,
      DocumentType.approvalNotice,
      DocumentType.denialNotice,
      DocumentType.requestForInfoNotice,
      DocumentType.withdrawalNotice,
    ]);
    const manyDocumentTypes = [
      DocumentType.appealAcknowledgment,
      DocumentType.approvalNotice,
      DocumentType.certification.certificationForm,
      DocumentType.certification[LeaveReason.care],
      DocumentType.certification.medicalCertification,
      DocumentType.denialNotice,
      DocumentType.identityVerification,
      DocumentType.medicalCertification,
      DocumentType.requestForInfoNotice,
      DocumentType.withdrawalNotice,
    ];
    const documents = manyDocumentTypes.map(
      (document_type) => new Document({ document_type })
    );

    const legalNotices = getLegalNotices(documents);

    for (const doc of legalNotices) {
      expect(legalNoticeTypes.has(doc.document_type)).toBe(true);
    }
  });
});
