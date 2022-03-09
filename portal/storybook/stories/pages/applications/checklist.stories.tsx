import Step, { ClaimSteps } from "src/models/Step";
import { Checklist } from "src/pages/applications/checklist";
import { DocumentType } from "src/models/Document";
import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
import { Props } from "types/common";
import React from "react";
import User from "src/models/User";
import claimantConfig from "src/flows/claimant";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

/**
 * Checklist step states are based on presence of validation warnings,
 * so in order to provide previews of the different states, we need
 * to generate warnings to prevent every step appearing Completed.
 */
function generateWarningsForStep(name: string) {
  const allSteps = Step.createClaimStepsFromMachine(claimantConfig);

  const step = allSteps.find((s) => s.name === name);

  return step?.fields.map((field) => {
    return {
      field: field.replace(/^claim./, ""),
      message: "Mocked warning",
      namespace: "applications",
    };
  });
}

/**
 * The various Checklist states our Storybook page will support previewing
 */
const scenarios = {
  "Verify Identity not started": {
    claim: new MockBenefitsApplicationBuilder().create(),
    documents: [],
    query: {},
    warnings: generateWarningsForStep(ClaimSteps.verifyId),
  },
  "Employment Information not started": {
    claim: new MockBenefitsApplicationBuilder().create(),
    documents: [],
    query: {},
    warnings: generateWarningsForStep(ClaimSteps.employerInformation),
  },
  "Leave Details not started": {
    claim: new MockBenefitsApplicationBuilder().create(),
    documents: [],
    query: {},
    warnings: generateWarningsForStep(ClaimSteps.leaveDetails),
  },
  "Part 1 ready for review": {
    claim: new MockBenefitsApplicationBuilder().noOtherLeave().create(),
    documents: [],
    query: {},
    warnings: [],
  },
  "Part 1 submitted": {
    claim: new MockBenefitsApplicationBuilder().submitted().create(),
    documents: [],
    query: {
      "part-one-submitted": "true",
    },
    warnings: [],
  },
  "Part 1 submitted, null Other Leave": {
    claim: new MockBenefitsApplicationBuilder()
      .submitted()
      .nullOtherLeave()
      .create(),
    documents: [],
    query: {
      "part-one-submitted": "true",
    },
    warnings: [],
  },
  "Part 2 submitted, no medical docs uploaded": {
    claim: new MockBenefitsApplicationBuilder()
      .paymentPrefSubmitted()
      .submitted()
      .create(),
    documents: [],
    query: {},
    warnings: generateWarningsForStep(ClaimSteps.payment),
  },
  "Part 2 submitted, caring leave with no certification form uploaded": {
    claim: new MockBenefitsApplicationBuilder()
      .paymentPrefSubmitted()
      .submitted()
      .caringLeaveReason()
      .create(),
    documents: [],
    query: {},
    warnings: generateWarningsForStep(ClaimSteps.payment),
  },

  "Proof of birth not uploaded (newborn)": {
    claim: new MockBenefitsApplicationBuilder()
      .paymentPrefSubmitted()
      .submitted()
      .bondingBirthLeaveReason()
      .create(),
    documents: [],
    query: {},
    warnings: [],
  },
  "Proof of placement not uploaded (adoption/foster)": {
    claim: new MockBenefitsApplicationBuilder()
      .paymentPrefSubmitted()
      .submitted()
      .bondingAdoptionLeaveReason()
      .create(),
    documents: [],
    query: {},
    warnings: [],
  },
  "Proof of birth not uploaded (future newborn)": {
    claim: new MockBenefitsApplicationBuilder()
      .paymentPrefSubmitted()
      .submitted()
      .bondingBirthLeaveReason()
      .hasFutureChild()
      .create(),
    documents: [],
    query: {},
    warnings: [],
  },
  "Proof of placement not uploaded (future adoption/foster)": {
    claim: new MockBenefitsApplicationBuilder()
      .paymentPrefSubmitted()
      .submitted()
      .bondingAdoptionLeaveReason()
      .hasFutureChild()
      .create(),
    documents: [],
    query: {},
    warnings: [],
  },
  "Docs uploaded, ready to submit": {
    claim: new MockBenefitsApplicationBuilder().complete().create(),
    documents: [
      {
        content_type: "image/jpeg",
        created_at: "2021-01-01",
        description: "",
        fineos_document_id: "",
        name: "",
        user_id: "",
        application_id: "",
        document_type: DocumentType.identityVerification,
      },
      {
        content_type: "image/jpeg",
        created_at: "2021-01-01",
        description: "",
        fineos_document_id: "",
        name: "",
        user_id: "",
        application_id: "",
        document_type: DocumentType.certification.medicalCertification,
      },
    ],
    query: {},
    warnings: [],
  },
};

export default {
  title: `Pages/Applications/Checklist`,
  component: Checklist,
  argTypes: {
    scenario: {
      control: {
        type: "radio",
        options: Object.keys(scenarios),
      },
    },
  },
  args: {
    scenario: Object.keys(scenarios)[0],
  },
};

export const DefaultStory = (
  args: Props<typeof Checklist> & { scenario: keyof typeof scenarios }
) => {
  const { claim, documents, query, warnings } = scenarios[args.scenario];
  const appLogic = useMockableAppLogic({
    benefitsApplications: {
      warningsLists: {
        [claim.application_id]: warnings ?? [],
      },
    },
  });

  return (
    <Checklist
      appLogic={appLogic}
      claim={claim}
      isLoadingDocuments={args.isLoadingDocuments}
      documents={documents}
      query={query || {}}
      user={new User({})}
    />
  );
};
