import Step, { ClaimSteps } from "src/models/Step";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { Checklist } from "src/pages/applications/checklist";
import DocumentCollection from "src/models/DocumentCollection";
import { DocumentType } from "src/models/Document";
import { MockBenefitsApplicationBuilder } from "tests/test-utils";
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
// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'name' implicitly has an 'any' type.
function generateWarningsForStep(name) {
  const allSteps = Step.createClaimStepsFromMachine(claimantConfig);

  const step = find(allSteps, { name });

  // @ts-expect-error ts-migrate(2532) FIXME: Object is possibly 'undefined'.
  return step.fields.map((field) => {
    return { field: field.replace(/^claim./, ""), message: "Mocked warning" };
  });
}

/**
 * The various Checklist states our Storybook page will support previewing
 */
const scenarios = {
  "Verify Identity not started": {
    claim: new MockBenefitsApplicationBuilder().create(),
    warnings: generateWarningsForStep(ClaimSteps.verifyId),
  },
  "Employment Information not started": {
    claim: new MockBenefitsApplicationBuilder().create(),
    warnings: generateWarningsForStep(ClaimSteps.employerInformation),
  },
  "Leave Details not started": {
    claim: new MockBenefitsApplicationBuilder().create(),
    warnings: generateWarningsForStep(ClaimSteps.leaveDetails),
  },
  "Part 1 ready for review": {
    claim: new MockBenefitsApplicationBuilder().noOtherLeave().create(),
  },
  "Part 1 submitted": {
    claim: new MockBenefitsApplicationBuilder().submitted().create(),
    query: {
      "part-one-submitted": "true",
    },
  },
  "Part 1 submitted, null Other Leave": {
    claim: new MockBenefitsApplicationBuilder()
      .submitted()
      .nullOtherLeave()
      .create(),
    query: {
      "part-one-submitted": "true",
    },
  },
  "Part 2 submitted, no medical docs uploaded": {
    claim: new MockBenefitsApplicationBuilder()
      .paymentPrefSubmitted()
      .submitted()
      .create(),
    warnings: generateWarningsForStep(ClaimSteps.payment),
  },
  "Part 2 submitted, caring leave with no certification form uploaded": {
    claim: new MockBenefitsApplicationBuilder()
      .paymentPrefSubmitted()
      .submitted()
      .caringLeaveReason()
      .create(),
    warnings: generateWarningsForStep(ClaimSteps.payment),
  },

  "Proof of birth not uploaded (newborn)": {
    claim: new MockBenefitsApplicationBuilder()
      .paymentPrefSubmitted()
      .submitted()
      .bondingBirthLeaveReason()
      .create(),
  },
  "Proof of placement not uploaded (adoption/foster)": {
    claim: new MockBenefitsApplicationBuilder()
      .paymentPrefSubmitted()
      .submitted()
      .bondingAdoptionLeaveReason()
      .create(),
  },
  "Proof of birth not uploaded (future newborn)": {
    claim: new MockBenefitsApplicationBuilder()
      .paymentPrefSubmitted()
      .submitted()
      .bondingBirthLeaveReason()
      .hasFutureChild()
      .create(),
  },
  "Proof of placement not uploaded (future adoption/foster)": {
    claim: new MockBenefitsApplicationBuilder()
      .paymentPrefSubmitted()
      .submitted()
      .bondingAdoptionLeaveReason()
      .hasFutureChild()
      .create(),
  },
  "Docs uploaded, ready to submit": {
    claim: new MockBenefitsApplicationBuilder().complete().create(),
    documents: [
      {
        document_type: DocumentType.identityVerification,
      },
      {
        document_type: DocumentType.certification.medicalCertification,
      },
    ],
  },
};

export default {
  title: `Pages/Applications/Checklist`,
  component: Checklist,
};

// @ts-expect-error ts-migrate(7006) FIXME: Parameter 'args' implicitly has an 'any' type.
export const DefaultStory = (args) => {
  // @ts-expect-error ts-migrate(7053) FIXME: Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
  const { claim, documents, query, warnings } = scenarios[args.scenario];

  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    benefitsApplications: {
      update: () => {},
      warningsLists: {
        [claim.application_id]: warnings || [],
      },
    },
    documents: {
      attachDocument: () => {},
      documents: new DocumentCollection(documents || []),
    },
    portalFlow: {
      getNextPageRoute: () => "/storybook-mock",
    },
  };

  return (
    <Checklist
      // @ts-expect-error ts-migrate(2740) FIXME: Type '{ appErrors: AppErrorInfoCollection; benefit... Remove this comment to see the full error message
      appLogic={appLogic}
      claim={claim}
      // @ts-expect-error ts-migrate(2322) FIXME: Type '(BenefitsApplicationDocument | ClaimDocument... Remove this comment to see the full error message
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
