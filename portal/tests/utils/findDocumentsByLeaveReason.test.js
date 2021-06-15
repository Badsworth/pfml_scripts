import Document, { DocumentType } from "../../src/models/Document";
import LeaveReason from "../../src/models/LeaveReason";
import findDocumentsByLeaveReason from "../../src/utils/findDocumentsByLeaveReason";

describe("findDocumentsByLeaveReason", () => {
  describe("when the useNewPlanProofs feature flag is on", () => {
    // TODO (CP-2306): Remove or disable useNewPlanProofs feature flag to coincide with FINEOS 6/25 udpate
    const documentsList = [
      new Document({
        document_type: DocumentType.certification[LeaveReason.medical],
      }),
      new Document({
        document_type: DocumentType.certification[LeaveReason.medical],
      }),
    ];

    beforeEach(() => {
      process.env.featureFlags = {
        useNewPlanProofs: true,
      };
    });

    it("returns an empty array when no documents are found", () => {
      const documents = findDocumentsByLeaveReason(
        documentsList,
        LeaveReason.bonding
      );
      expect(documents).toEqual([]);
    });

    it("returns an array with all of the matching documents when the leave reason matches the doc type", () => {
      const testDocs = [
        new Document({ document_type: DocumentType.identityVerification }),
        new Document({ document_type: DocumentType.identityVerification }),
      ];
      const documents = findDocumentsByLeaveReason(
        [...documentsList, ...testDocs],
        LeaveReason.medical
      );

      expect(documents).toHaveLength(2);
      expect(documents).toEqual(documentsList);
    });

    it("returns an empty array when the documents list is empty", () => {
      const documents = findDocumentsByLeaveReason([], LeaveReason.medical);
      expect(documents).toEqual([]);
    });
  });

  describe("when the useNewPlanProofs feature flag is off", () => {
    // TODO (CP-2306): Remove or disable useNewPlanProofs feature flag to coincide with FINEOS 6/25 udpate
    const documentsList = [
      new Document({
        document_type: DocumentType.certification.medicalCertification,
      }),
      new Document({
        document_type: DocumentType.certification[LeaveReason.medical],
      }),
      new Document({
        document_type: DocumentType.certification[LeaveReason.care],
      }),
      new Document({
        document_type: DocumentType.certification[LeaveReason.bonding],
      }),
      new Document({
        document_type: DocumentType.certification[LeaveReason.pregnancy],
      }),
    ];

    it("only filters using the State managed Paid Leave Confirmation document type", () => {
      process.env.featureFlags = {
        useNewPlanProofs: false,
      };
      const documents = findDocumentsByLeaveReason(
        documentsList,
        LeaveReason.medical
      );
      expect(documents).toHaveLength(1);
      expect(documents[0].document_type).toEqual(
        DocumentType.certification.medicalCertification
      );
    });
  });

  it("decouples plan proof filtering from showCaringLeaveType flag", () => {
    // When useNewPlanProofs is false but showCaringLeaveType is true, the new plan proofs should not be used in filtering
    // TODO (CP-1989): Remove showCaringLeaveType flag once caring leave is made available in Production
    // TODO (CP-2306): Remove or disable useNewPlanProofs feature flag to coincide with FINEOS 6/25 udpate
    const documentsList = [
      new Document({
        document_type: DocumentType.certification.medicalCertification,
      }),
      new Document({
        document_type: DocumentType.certification[LeaveReason.medical],
      }),
      new Document({
        document_type: DocumentType.certification[LeaveReason.care],
      }),
      new Document({
        document_type: DocumentType.certification[LeaveReason.bonding],
      }),
      new Document({
        document_type: DocumentType.certification[LeaveReason.pregnancy],
      }),
    ];

    process.env.featureFlags = {
      useNewPlanProofs: false,
      showCaringLeaveType: true,
    };
    const documents = findDocumentsByLeaveReason(
      documentsList,
      LeaveReason.medical
    );
    expect(documents).toHaveLength(1);
    expect(documents[0].document_type).toEqual(
      DocumentType.certification.medicalCertification
    );
  });
});
