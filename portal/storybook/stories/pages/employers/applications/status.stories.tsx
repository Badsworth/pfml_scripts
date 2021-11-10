import DocumentCollection from "src/models/DocumentCollection";
import { DocumentType } from "src/models/Document";
import { MockEmployerClaimBuilder } from "tests/test-utils";
import React from "react";
import { Status } from "src/pages/employers/applications/status";
import User from "src/models/User";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

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

  const documentData = {
    application_id: "mock-application-id",
    content_type: "application/pdf",
    created_at: "2020-01-02",
    fineos_document_id: 202020,
    name: "Your Document",
  };

  if (document === "Approval notice") {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'document_type' does not exist on type '{... Remove this comment to see the full error message
    documentData.document_type = DocumentType.approvalNotice;
  } else if (document === "Denial notice" || document === "Multiple") {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'document_type' does not exist on type '{... Remove this comment to see the full error message
    documentData.document_type = DocumentType.denialNotice;
  } else if (document === "Request for info") {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'document_type' does not exist on type '{... Remove this comment to see the full error message
    documentData.document_type = DocumentType.requestForInfoNotice;
  } else if (document === "Other") {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 'document_type' does not exist on type '{... Remove this comment to see the full error message
    documentData.document_type = DocumentType.identityVerification;
  }

  let documentsMap;
  if (document === "None") {
    documentsMap = new Map([["mock-absence-id", new DocumentCollection()]]);
  } else if (document === "Multiple") {
    documentsMap = new Map([
      [
        "mock-absence-id",
        new DocumentCollection([
          // @ts-expect-error ts-migrate(2322) FIXME: Type '{ application_id: string; content_type: stri... Remove this comment to see the full error message
          { ...documentData },
          // @ts-expect-error ts-migrate(2322) FIXME: Type '{ document_type: "Request for more Informati... Remove this comment to see the full error message
          {
            ...documentData,
            document_type: DocumentType.requestForInfoNotice,
          },
        ]),
      ],
    ]);
  } else {
    documentsMap = new Map([
      // @ts-expect-error ts-migrate(2322) FIXME: Type '{ application_id: string; content_type: stri... Remove this comment to see the full error message
      ["mock-absence-id", new DocumentCollection([{ ...documentData }])],
    ]);
  }

  const claim = claimBuilder.create();
  const appLogic = useMockableAppLogic({
    employers: {
      claim,
      claimDocumentsMap: documentsMap,
    },
  });

  return <Status appLogic={appLogic} claim={claim} user={new User({})} />;
};
