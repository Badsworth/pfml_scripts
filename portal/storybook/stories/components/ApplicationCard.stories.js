import Document, { DocumentType } from "src/models/Document";
import AppErrorInfo from "src/models/AppErrorInfo";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { ApplicationCard } from "src/components/ApplicationCard";
import BenefitsApplication from "src/models/BenefitsApplication";
import { MockBenefitsApplicationBuilder } from "tests/test-utils";
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
          "Submitted + Denial notice",
          "Completed",
          "Future Newborn + No cert",
          "Future Adoption + No cert",
          "Caregiver + No cert",
          "Approved",
          "Denied",
        ],
      },
    },
    errors: {
      defaultValue: "None",
      control: { type: "radio", options: ["DocumentsLoadError"] },
    },
  },
};

export const Story = ({ claim, documents, ...args }) => {
  let attachedDocuments = [];
  let claimAttrs;
  const errors = [];

  if (claim === "Empty") {
    claimAttrs = new MockBenefitsApplicationBuilder().create();
  } else if (claim === "Hybrid leave") {
    claimAttrs = new MockBenefitsApplicationBuilder()
      .employed()
      .continuous()
      .reducedSchedule()
      .create();
  } else if (claim === "Intermittent leave") {
    claimAttrs = new MockBenefitsApplicationBuilder()
      .employed()
      .intermittent()
      .create();
  } else if (claim === "Submitted") {
    claimAttrs = new MockBenefitsApplicationBuilder().submitted().create();
  } else if (claim === "Submitted + Denial notice") {
    claimAttrs = new MockBenefitsApplicationBuilder().submitted().create();
    attachedDocuments = [
      new Document({
        created_at: "2021-01-15",
        document_type: DocumentType.denialNotice,
        fineos_document_id: "a",
      }),
    ];
  } else if (claim === "Completed") {
    claimAttrs = new MockBenefitsApplicationBuilder().completed().create();
  } else if (claim === "Future Newborn + No cert") {
    claimAttrs = new MockBenefitsApplicationBuilder()
      .completed()
      .bondingBirthLeaveReason()
      .hasFutureChild()
      .create();
    attachedDocuments = [
      new Document({
        created_at: "2021-01-15",
        document_type: DocumentType.identityVerification,
        fineos_document_id: "a",
      }),
    ];
  } else if (claim === "Future Adoption + No cert") {
    claimAttrs = new MockBenefitsApplicationBuilder()
      .completed()
      .bondingAdoptionLeaveReason()
      .hasFutureChild()
      .create();
    attachedDocuments = [
      new Document({
        created_at: "2021-01-15",
        document_type: DocumentType.identityVerification,
        fineos_document_id: "a",
      }),
    ];
  } else if (claim === "Caregiver + No cert") {
    claimAttrs = new MockBenefitsApplicationBuilder()
      .completed()
      .caringLeaveReason()
      .create();
    attachedDocuments = [
      new Document({
        created_at: "2021-01-15",
        document_type: DocumentType.identityVerification,
        fineos_document_id: "a",
      }),
    ];
  } else if (claim === "Approved") {
    claimAttrs = new MockBenefitsApplicationBuilder().completed().create();
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
    claimAttrs = new MockBenefitsApplicationBuilder().completed().create();
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

  if (args.errors === "DocumentsLoadError") {
    // There wouldn't be documents in this case
    attachedDocuments = [];

    errors.push(
      new AppErrorInfo({
        meta: { application_id: claimAttrs.application_id },
        name: "DocumentsLoadError",
      })
    );
  }

  const appLogic = {
    appErrors: new AppErrorInfoCollection(errors),
  };

  return (
    <ApplicationCard
      appLogic={appLogic}
      claim={new BenefitsApplication(claimAttrs)}
      {...args}
      documents={attachedDocuments}
    />
  );
};
