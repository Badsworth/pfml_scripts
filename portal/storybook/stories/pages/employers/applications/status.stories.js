import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import ClaimDocument from "src/models/ClaimDocument";
import DocumentCollection from "src/models/DocumentCollection";
import { DocumentType } from "src/models/Document";
import { MockEmployerClaimBuilder } from "tests/test-utils";
import React from "react";
import { Status } from "src/pages/employers/applications/status";

export default {
  title: "Pages/Employers/Applications/Status",
  component: Status,
  argTypes: {
    leaveDurationType: {
      defaultValue: ["Continuous"],
      control: {
        type: "check",
        options: ["Continuous", "Intermittent", "Reduced"],
      },
    },
    status: {
      defaultValue: "Approved",
      control: {
        type: "radio",
        options: [
          "Approved",
          "Declined",
          "Closed",
          "Completed",
          "Adjudication",
          "Intake In Progress",
        ],
      },
    },
    document: {
      defaultValue: "Approval notice",
      control: {
        type: "radio",
        options: [
          "Approval notice",
          "Denial notice",
          "Request for info",
          "Other",
          "Multiple",
          "None",
        ],
      },
    },
  },
};

export const Default = ({ status, document, leaveDurationType }) => {
  const claim = new MockEmployerClaimBuilder()
    .status(status)
    .bondingLeaveReason();

  if (leaveDurationType.includes("Continuous")) {
    claim.continuous();
  }

  if (leaveDurationType.includes("Intermittent")) {
    claim.intermittent();
  }

  if (leaveDurationType.includes("Reduced")) {
    claim.reducedSchedule();
  }

  const documentData = {
    application_id: "mock-application-id",
    content_type: "application/pdf",
    created_at: "2020-01-02",
    fineos_document_id: 202020,
    name: "Your Document",
  };

  if (document === "Approval notice") {
    documentData.document_type = DocumentType.approvalNotice;
  } else if (document === "Denial notice" || document === "Multiple") {
    documentData.document_type = DocumentType.denialNotice;
  } else if (document === "Request for info") {
    documentData.document_type = DocumentType.requestForInfoNotice;
  } else if (document === "Other") {
    documentData.document_type = DocumentType.identityVerification;
  }

  let documents;
  if (document === "None") {
    documents = new DocumentCollection();
  } else if (document === "Multiple") {
    documents = new DocumentCollection([
      new ClaimDocument({ ...documentData }),
      new ClaimDocument({
        ...documentData,
        document_type: DocumentType.requestForInfoNotice,
      }),
    ]);
  } else {
    documents = new DocumentCollection([
      new ClaimDocument({ ...documentData }),
    ]);
  }

  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    employers: {
      claim: claim.create(),
      documents,
      downloadDocument: () => {},
      loadClaim: () => {},
      loadDocuments: () => {},
    },
    setAppErrors: () => {},
  };

  const query = { absence_id: "mock-absence-id" };

  return <Status appLogic={appLogic} query={query} />;
};
