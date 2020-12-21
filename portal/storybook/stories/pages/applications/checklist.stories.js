import Document, { DocumentType } from "src/models/Document";
import Step, { ClaimSteps } from "src/models/Step";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { Checklist } from "src/pages/applications/checklist";
import DocumentCollection from "src/models/DocumentCollection";
import { MockClaimBuilder } from "tests/test-utils";
import React from "react";
import claimantConfig from "src/flows/claimant";
import { find } from "lodash";

/**
 * Checklist step states are based on presence of validation warnings,
 * so in order to provide previews of the different states, we need
 * to generate warnings to prevent every step appearing Completed.
 * @param {string} name
 * @returns {{ field: string, message: string }[]}
 */
function generateWarningsForStep(name) {
  const allSteps = Step.createClaimStepsFromMachine(claimantConfig);

  const step = find(allSteps, { name });

  return step.fields.map((field) => {
    return { field: field.replace(/^claim./, ""), message: "Mocked warning" };
  });
}

/**
 * The various Checklist states our Storybook page will support previewing
 */
const scenarios = {
  "Verify Identity not started": {
    claim: new MockClaimBuilder().create(),
    warnings: generateWarningsForStep(ClaimSteps.verifyId),
  },
  "Employment Information not started": {
    claim: new MockClaimBuilder().create(),
    warnings: generateWarningsForStep(ClaimSteps.employerInformation),
  },
  "Leave Details not started": {
    claim: new MockClaimBuilder().create(),
    warnings: generateWarningsForStep(ClaimSteps.leaveDetails),
  },
  "Part 1 ready for review": {
    claim: new MockClaimBuilder().noOtherLeave().create(),
  },
  "Part 1 submitted, payments not started": {
    claim: new MockClaimBuilder().noOtherLeave().submitted().create(),
    query: {
      "part-one-submitted": "true",
    },
  },
  "Part 2 submitted, no medical docs uploaded": {
    claim: new MockClaimBuilder().paymentPrefSubmitted().submitted().create(),
    warnings: generateWarningsForStep(ClaimSteps.payment),
  },
  "Proof of birth not uploaded (newborn)": {
    claim: new MockClaimBuilder()
      .paymentPrefSubmitted()
      .submitted()
      .bondingBirthLeaveReason()
      .create(),
  },
  "Proof of placement not uploaded (adoption/foster)": {
    claim: new MockClaimBuilder()
      .paymentPrefSubmitted()
      .submitted()
      .bondingAdoptionLeaveReason()
      .create(),
  },
  "Proof of birth not uploaded (future newborn)": {
    claim: new MockClaimBuilder()
      .paymentPrefSubmitted()
      .submitted()
      .bondingBirthLeaveReason()
      .hasFutureChild()
      .create(),
  },
  "Proof of placement not uploaded (future adoption/foster)": {
    claim: new MockClaimBuilder()
      .paymentPrefSubmitted()
      .submitted()
      .bondingAdoptionLeaveReason()
      .hasFutureChild()
      .create(),
  },
  "Docs uploaded, ready to submit": {
    claim: new MockClaimBuilder().complete().create(),
    documents: [
      new Document({
        document_type: DocumentType.identityVerification,
      }),
      new Document({
        document_type: DocumentType.medicalCertification,
      }),
    ],
  },
};

export default {
  title: `Pages/Applications/Checklist`,
  component: Checklist,
};

export const DefaultStory = (args) => {
  const { claim, documents, query, warnings } = scenarios[args.scenario];

  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    claims: {
      update: () => {},
      warningsLists: {
        [claim.application_id]: warnings || [],
      },
    },
    documents: {
      attachDocument: () => {},
      documents: new DocumentCollection(documents || []),
    },
  };

  return (
    <Checklist
      appLogic={appLogic}
      claim={claim}
      documents={appLogic.documents.documents.items}
      query={query || {}}
    />
  );
};

DefaultStory.argTypes = {
  scenario: {
    defaultValue: Object.keys(scenarios)[0],
    control: {
      type: "radio",
      options: Object.keys(scenarios),
    },
  },
};
