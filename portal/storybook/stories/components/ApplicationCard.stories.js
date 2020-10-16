import Document, { DocumentType } from "src/models/Document";
import AppErrorInfo from "src/models/AppErrorInfo";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { ApplicationCard } from "src/components/ApplicationCard";
import Claim from "src/models/Claim";
import { MockClaimBuilder } from "tests/test-utils";
import React from "react";

export default {
  title: "Components/ApplicationCard",
  component: ApplicationCard,
  args: {
    number: 1,
  },
  argTypes: {
    claim: {
      defaultValue: "Submitted",
      control: {
        type: "radio",
        options: [
          "Empty",
          "Hybrid leave",
          "Intermittent leave",
          "Submitted",
          "Completed",
          "Approved",
          "Denied",
        ],
      },
    },
    errors: {
      defaultValue: "None",
      control: { type: "radio", options: ["DocumentsRequestError"] },
    },
  },
};

export const Story = ({ claim, documents, ...args }) => {
  let attachedDocuments = [];
  let claimAttrs;
  const errors = [];

  if (claim === "Empty") {
    claimAttrs = new MockClaimBuilder().create();
  } else if (claim === "Hybrid leave") {
    claimAttrs = new MockClaimBuilder().continuous().reducedSchedule().create();
  } else if (claim === "Intermittent leave") {
    claimAttrs = new MockClaimBuilder().intermittent().create();
  } else if (claim === "Submitted") {
    claimAttrs = new MockClaimBuilder().submitted().create();
  } else if (claim === "Completed") {
    claimAttrs = new MockClaimBuilder().completed().create();
  } else if (claim === "Approved") {
    claimAttrs = new MockClaimBuilder().completed().create();
    attachedDocuments = [
      new Document({
        created_at: "2021-01-15",
        document_type: DocumentType.requestForInfoNotice,
        fineos_document_id: "a",
      }),
      new Document({
        created_at: "2021-01-30",
        document_type: DocumentType.approvalNotice,
        fineos_document_id: "b",
      }),
    ];
  } else if (claim === "Denied") {
    claimAttrs = new MockClaimBuilder().completed().create();
    attachedDocuments = [
      new Document({
        created_at: "2021-01-15",
        document_type: DocumentType.requestForInfoNotice,
        fineos_document_id: "a",
      }),
      new Document({
        created_at: "2021-01-30",
        document_type: DocumentType.denialNotice,
        fineos_document_id: "b",
      }),
    ];
  }

  if (args.errors === "DocumentsRequestError") {
    // There wouldn't be documents in this case
    attachedDocuments = [];

    errors.push(
      new AppErrorInfo({
        meta: { application_id: claimAttrs.application_id },
        name: "DocumentsRequestError",
      })
    );
  }

  const appLogic = {
    appErrors: new AppErrorInfoCollection(errors),
  };

  return (
    <ApplicationCard
      appLogic={appLogic}
      claim={new Claim(claimAttrs)}
      {...args}
      documents={attachedDocuments}
    />
  );
};
