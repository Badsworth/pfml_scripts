import Document, { DocumentType } from "../../src/models/Document";
import LeaveReason from "../../src/models/LeaveReason";
import { MockClaimBuilder } from "../test-utils";
import findDocumentsByLeaveReason from "../../src/utils/findDocumentsByLeaveReason";

describe("findDocumentsByLeaveReason", () => {
  const medicalClaim = new MockClaimBuilder().medicalLeaveReason().create();
  const bondingClaim = new MockClaimBuilder()
    .bondingBirthLeaveReason()
    .create();

  describe("when the showCaringLeave feature flag is on", () => {
    // TODO (CP-1989): Remove feature flag and refactor tests
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
        showCaringLeaveType: true,
      };
    });

    it("returns an empty array when no documents are found", () => {
      const documents = findDocumentsByLeaveReason(documentsList, bondingClaim);
      expect(documents).toEqual([]);
    });

    it("returns an array with all of the matching documents when the leave reason matches the doc type", () => {
      const testDocs = [
        new Document({ document_type: DocumentType.identityVerification }),
        new Document({ document_type: DocumentType.identityVerification }),
      ];
      const documents = findDocumentsByLeaveReason(
        [...documentsList, ...testDocs],
        medicalClaim
      );

      expect(documents).toHaveLength(2);
      expect(documents).toEqual(documentsList);
    });

    it("returns an empty array when the documents list is empty", () => {
      const documents = findDocumentsByLeaveReason([], medicalClaim);
      expect(documents).toEqual([]);
    });
  });

  describe("when the showCaringLeave feature flag is off", () => {
    // TODO (CP-1989): Remove feature flag-related tests
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
        showCaringLeaveType: false,
      };
      const documents = findDocumentsByLeaveReason(documentsList, medicalClaim);
      expect(documents).toHaveLength(1);
      expect(documents[0].document_type).toEqual(
        DocumentType.certification.medicalCertification
      );
    });
  });
});
