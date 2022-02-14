import { BenefitsApplicationDocument, DocumentType } from "src/models/Document";
import LeaveReason, { LeaveReasonType } from "src/models/LeaveReason";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import { ApplicationCard } from "src/components/ApplicationCard";
import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
import { Props } from "types/common";
import React from "react";
import { Story } from "@storybook/react";
import { createMockBenefitsApplicationDocument } from "lib/mock-helpers/createMockDocument";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Features/Applications/ApplicationCard",
  component: ApplicationCard,
  args: {
    claim: "Started, no EIN",
    Reason: "",
    Notices: "No notices",
  },
  argTypes: {
    claim: {
      control: {
        type: "radio",
        options: [
          "Started, no EIN",
          "Started, with EIN",
          "Part 1 submitted",
          "Completed",
        ],
      },
    },
    Reason: {
      control: {
        type: "radio",
        options: ["", ...Object.values(LeaveReason)],
      },
    },
    Notices: {
      control: {
        type: "radio",
        options: ["Has notices", "No notices", "Loading"],
      },
    },
  },
};

const claimScenarios = {
  "Started, no EIN": new MockBenefitsApplicationBuilder().create(),
  "Started, with EIN": new MockBenefitsApplicationBuilder().employed().create(),
  "Part 1 submitted": new MockBenefitsApplicationBuilder().submitted().create(),
  Completed: new MockBenefitsApplicationBuilder().completed().create(),
} as const;

type Args = Omit<Props<typeof ApplicationCard>, "claim"> & {
  claim: keyof typeof claimScenarios;
  Notices: "Has notices" | "No notices" | "Loading";
  Reason: LeaveReasonType;
};

const Template: Story<Args> = (args) => {
  const appLogic = useMockableAppLogic({
    documents: {
      loadAll: () => Promise.resolve(),
      isLoadingClaimDocuments: () => {
        return args.Notices === "Loading";
      },
      documents: new ApiResourceCollection<BenefitsApplicationDocument>(
        "fineos_document_id",
        args.Notices === "Has notices"
          ? [
              createMockBenefitsApplicationDocument({
                document_type: DocumentType.requestForInfoNotice,
                fineos_document_id: "test 1",
              }),
              createMockBenefitsApplicationDocument({
                document_type: DocumentType.denialNotice,
                fineos_document_id: "test 2",
              }),
              createMockBenefitsApplicationDocument({
                document_type:
                  DocumentType.certification[
                    "Serious Health Condition - Employee"
                  ],
                fineos_document_id: "test 3",
              }),
            ]
          : []
      ),
    },
  });

  const defaultReason = args.claim === "Completed" ? LeaveReason.medical : null;
  const claim = claimScenarios[args.claim];
  claim.leave_details = claim.leave_details ?? {};
  claim.leave_details.reason = args.Reason ? args.Reason : defaultReason;

  return <ApplicationCard {...args} claim={claim} appLogic={appLogic} />;
};

export const Started = Template.bind({});

export const Submitted = Template.bind({});
Submitted.args = {
  claim: "Part 1 submitted",
};

export const Completed = Template.bind({});
Completed.args = {
  claim: "Completed",
};
