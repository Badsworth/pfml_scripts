import Document, { DocumentType } from "src/models/Document";
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
  },
};

export const Story = ({ claim, documents, ...args }) => {
  let attachedDocuments = [];
  let claimAttrs;

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

  return (
    <ApplicationCard
      claim={new Claim(claimAttrs)}
      {...args}
      documents={attachedDocuments}
    />
  );
};
