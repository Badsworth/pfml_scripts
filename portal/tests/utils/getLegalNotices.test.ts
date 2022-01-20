import { DocumentType } from "../../src/models/Document";
import LeaveReason from "../../src/models/LeaveReason";
import getLegalNotices from "../../src/utils/getLegalNotices";

describe("getLegalNotices", () => {
  it("filters out all non-legal notices", () => {
    const legalNoticeTypes = new Set<string>([
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
      DocumentType.maximumWeeklyBenefitChangeNotice,
      DocumentType.benefitAmountChangeNotice,
      DocumentType.leaveAllotmentChangeNotice,
      DocumentType.approvedTimeCancelled,
      DocumentType.changeRequestApproved,
      DocumentType.changeRequestDenied,
    ];
    const documents = manyDocumentTypes.map((document_type) => {
      return {
        document_type,
        content_type: "application/pdf",
        created_at: "2021-05-01",
        description: "",
        fineos_document_id: "mock-doc-id",
        name: "",
      };
    });

    const legalNotices = getLegalNotices(documents);

    for (const doc of legalNotices) {
      expect(legalNoticeTypes.has(doc.document_type)).toBe(true);
    }
  });
});
