import {
  DocumentType,
  filterByApplication,
  findDocumentsByLeaveReason,
  findDocumentsByTypes,
  getLegalNotices,
} from "src/models/Document";
import LeaveReason from "src/models/LeaveReason";
import { createMockBenefitsApplicationDocument } from "lib/mock-helpers/createMockDocument";

describe("filterByApplication", () => {
  it("returns only Documents associated with the given application", () => {
    const applicationADocument1 = createMockBenefitsApplicationDocument({
      application_id: "a",
    });
    const applicationADocument2 = createMockBenefitsApplicationDocument({
      application_id: "a",
    });
    const applicationBDocument1 = createMockBenefitsApplicationDocument({
      application_id: "b",
    });

    const documents = [
      applicationADocument1,
      applicationADocument2,
      applicationBDocument1,
    ];

    expect(filterByApplication(documents, "a")).toEqual([
      applicationADocument1,
      applicationADocument2,
    ]);
    expect(filterByApplication(documents, "b")).toEqual([
      applicationBDocument1,
    ]);
  });
});

describe("findDocumentsByLeaveReason", () => {
  const documentsList = [
    createMockBenefitsApplicationDocument({
      document_type: DocumentType.certification[LeaveReason.medical],
    }),
    createMockBenefitsApplicationDocument({
      document_type: DocumentType.certification[LeaveReason.medical],
    }),
  ];

  it("returns an empty array when no documents are found", () => {
    const documents = findDocumentsByLeaveReason(
      documentsList,
      LeaveReason.bonding
    );
    expect(documents).toEqual([]);
  });

  it("returns an array with all of the matching documents when the leave reason matches the doc type", () => {
    const testDocs = [
      createMockBenefitsApplicationDocument({
        document_type: DocumentType.identityVerification,
      }),
      createMockBenefitsApplicationDocument({
        document_type: DocumentType.identityVerification,
      }),
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

describe("findDocumentsByTypes", () => {
  describe("when no documents are found", () => {
    it("returns an empty array", () => {
      const documentsList = [
        createMockBenefitsApplicationDocument({
          document_type: DocumentType.identityVerification,
        }),
        createMockBenefitsApplicationDocument({
          document_type: DocumentType.certification.certificationForm,
        }),
      ];
      const documents = findDocumentsByTypes(documentsList, [
        DocumentType.certification["Child Bonding"],
      ]);

      expect(documents).toEqual([]);
    });
  });

  describe("when the documents list has multiple matching documents", () => {
    it("returns an array with all of the matching documents", () => {
      const documentsList = [
        createMockBenefitsApplicationDocument({
          document_type: DocumentType.identityVerification,
        }),
        createMockBenefitsApplicationDocument({
          document_type: DocumentType.identityVerification,
        }),
        createMockBenefitsApplicationDocument({
          document_type: DocumentType.certification.certificationForm,
        }),
      ];
      const documents = findDocumentsByTypes(documentsList, [
        DocumentType.identityVerification,
      ]);

      expect(documents).toHaveLength(2);
    });
  });

  describe("when the documents list is empty", () => {
    it("returns an empty array", () => {
      const documents = findDocumentsByTypes(
        [],
        [DocumentType.identityVerification]
      );
      expect(documents).toEqual([]);
    });
  });

  it("returns matching documents even if casing of document_type is different", () => {
    const documentsList = [
      createMockBenefitsApplicationDocument({
        document_type: DocumentType.identityVerification,
      }),
    ];
    const documents = findDocumentsByTypes(documentsList, [
      // @ts-expect-error Intentionally using a different casing
      DocumentType.identityVerification.toLocaleLowerCase(),
    ]);

    expect(documents).toHaveLength(1);
  });

  it("returns matching documents when there are multiple document types", () => {
    const documentsList = [
      createMockBenefitsApplicationDocument({
        document_type: DocumentType.identityVerification,
      }),
      createMockBenefitsApplicationDocument({
        document_type: DocumentType.certification.certificationForm,
      }),
    ];
    const documents = findDocumentsByTypes(documentsList, [
      DocumentType.identityVerification,
      DocumentType.certification.certificationForm,
    ]);

    expect(documents).toHaveLength(2);
  });
});

describe("getLegalNotices", () => {
  it("filters out notices of non-legal type", () => {
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
