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
        ],
      },
    },
    documents: {
      defaultValue: "Empty",
      control: {
        type: "radio",
        options: ["Empty", "With Legal Notice (Claim must be completed)"],
      },
    },
  },
};

export const Story = ({ claim, documents, ...args }) => {
  let attachedDocuments, claimAttrs;

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
  }

  switch (documents) {
    case "Empty":
      attachedDocuments = [];
      break;
    case "With Legal Notice (Claim must be completed)": // TODO (CP-1111): Update to display all notice types
      attachedDocuments = [
        new Document({
          created_at: "1/1/2021",
          document_type: DocumentType.notices,
        }),
      ];
      break;
  }

  return (
    <ApplicationCard
      claim={new Claim(claimAttrs)}
      {...args}
      documents={attachedDocuments}
    />
  );
};
