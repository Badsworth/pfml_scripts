import { BenefitsApplicationDocument, DocumentType } from "src/models/Document";
import DocumentCollection from "src/models/DocumentCollection";
import { MockEmployerClaimBuilder } from "tests/test-utils/mock-model-builder";
import React from "react";
import { Status } from "src/pages/employers/applications/status";
import User from "src/models/User";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Employers/Applications/Status",
  component: Status,
  args: {
    document: "Approval notice",
    leaveDurationType: ["Continuous"],
    status: "Approved",
  },
  argTypes: {
    leaveDurationType: {
      control: {
        type: "check",
        options: ["Continuous", "Intermittent", "Reduced"],
      },
    },
    status: {
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

export const Default = ({
  status,
  document,
  leaveDurationType,
}: {
  status: string;
  document: string;
  leaveDurationType: string;
}) => {
  let claimBuilder = new MockEmployerClaimBuilder()
    .status(status)
    .bondingLeaveReason();

  if (leaveDurationType.includes("Continuous")) {
    claimBuilder = claimBuilder.continuous();
  }

  if (leaveDurationType.includes("Intermittent")) {
    claimBuilder = claimBuilder.intermittent();
  }

  if (leaveDurationType.includes("Reduced")) {
    claimBuilder = claimBuilder.reducedSchedule();
  }

  const documentData: BenefitsApplicationDocument = {
    application_id: "mock-application-id",
    content_type: "application/pdf",
    description: "",
    document_type: DocumentType.identityVerification,
    created_at: "2020-01-02",
    fineos_document_id: "202020",
    name: "Your Document",
    user_id: "",
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
  const claim = claimBuilder.create();

  let documentsMap;
  if (document === "None") {
    documentsMap = new Map([
      [claim.fineos_absence_id, new DocumentCollection()],
    ]);
  } else if (document === "Multiple") {
    documentsMap = new Map([
      [
        claim.fineos_absence_id,
        new DocumentCollection([
          { ...documentData },
          {
            ...documentData,
            document_type: DocumentType.requestForInfoNotice,
          },
        ]),
      ],
    ]);
  } else {
    documentsMap = new Map([
      [claim.fineos_absence_id, new DocumentCollection([{ ...documentData }])],
    ]);
  }

  const appLogic = useMockableAppLogic({
    employers: {
      claim,
      claimDocumentsMap: documentsMap,
    },
  });

  return <Status appLogic={appLogic} claim={claim} user={new User({})} />;
};
