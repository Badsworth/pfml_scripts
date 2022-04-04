import BenefitsApplication, {
  ReasonQualifier,
} from "src/models/BenefitsApplication";
import { BenefitsApplicationDocument, DocumentType } from "src/models/Document";
import { Props, ValuesOf } from "types/common";
import Step, { ClaimSteps } from "src/models/Step";
import { Checklist } from "src/pages/applications/checklist";
import { Issue } from "src/errors";
import LeaveReason from "src/models/LeaveReason";
import { MockBenefitsApplicationBuilder } from "lib/mock-helpers/mock-model-builder";
import React from "react";
import { Story } from "@storybook/react";
import User from "src/models/User";
import claimantConfig from "src/flows/claimant";
import { createMockBenefitsApplicationDocument } from "lib/mock-helpers/createMockDocument";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

/**
 * Checklist step states are based on presence of validation warnings,
 * so in order to provide previews of the different states, we need
 * to generate warnings to prevent every step appearing Completed.
 */
function generateWarningsForStep(name: string): Issue[] | undefined {
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
interface Scenario {
  claim?: BenefitsApplication;
  documents?: BenefitsApplicationDocument[];
  warnings?: Issue[];
}

const scenarios: {
  [name: string]: Scenario;
} = {
  "1. Verify ID - Not started": {
    warnings: generateWarningsForStep(ClaimSteps.verifyId),
  },
  "2. Employment Information - In progress": {
    claim: new MockBenefitsApplicationBuilder().employed().create(),
    warnings: generateWarningsForStep(ClaimSteps.employerInformation),
  },
  "3. Leave Details - Not started": {
    warnings: generateWarningsForStep(ClaimSteps.leaveDetails),
  },
  "4. Other Leave - Not started": {
    warnings: generateWarningsForStep(ClaimSteps.otherLeave),
  },
  "5. Review and confirm - Not started": {
    claim: new MockBenefitsApplicationBuilder().noOtherLeave().create(),
  },
  "6 & 7 - Not started": {
    claim: new MockBenefitsApplicationBuilder().submitted().create(),
  },
  "8 & 9 - No uploads": {
    claim: new MockBenefitsApplicationBuilder()
      .paymentPrefSubmitted()
      .taxPrefSubmitted()
      .submitted()
      .create(),
    warnings: generateWarningsForStep(ClaimSteps.payment),
  },
  "All steps complete": {
    claim: new MockBenefitsApplicationBuilder().complete().create(),
    documents: [
      createMockBenefitsApplicationDocument({
        document_type: DocumentType.identityVerification,
      }),
      createMockBenefitsApplicationDocument({
        document_type: DocumentType.certification.medicalCertification,
      }),
    ],
  },
};

export default {
  title: `Pages/Applications/Checklist`,
  argTypes: {
    "Active step(s)": {
      options: Object.keys(scenarios),
      control: {
        type: "select",
      },
    },
    "Leave reason": {
      options: Object.values(LeaveReason).filter(
        (reason) =>
          // We don't support applying for Military yet, so this can result in broken strings if rendered
          !reason.includes("Military")
      ),
      control: {
        type: "select",
      },
    },
    "Reason qualifier": {
      options: [""].concat(Object.values(ReasonQualifier)),
      control: {
        type: "select",
      },
    },
    query: {
      options: [
        "None",
        "part-one-submitted",
        "payment-pref-submitted",
        "tax-pref-submitted",
      ],
      control: {
        type: "radio",
      },
    },
  },
  args: {
    "Active step(s)": Object.keys(scenarios)[0],
    "Leave reason": LeaveReason.medical,
    "Future child birth/placement": false,
    isLoadingDocuments: false,
  },
};

type Args = Props<typeof Checklist> & {
  "Active step(s)": keyof typeof scenarios;
  "Future child birth/placement": boolean;
  "Leave reason": ValuesOf<typeof LeaveReason>;
  "Reason qualifier": ValuesOf<typeof ReasonQualifier>;
  query: string;
};

const Template: Story<Args> = (args) => {
  const {
    claim: initialClaim,
    documents,
    warnings,
  } = scenarios[args["Active step(s)"]];
  const claim = initialClaim ?? new MockBenefitsApplicationBuilder().create();

  // Further configure the mock claim using more granular args.
  // These influences content in the Checklist:
  claim.leave_details.has_future_child_date =
    args["Future child birth/placement"];
  claim.leave_details.reason = args["Leave reason"];
  claim.leave_details.reason_qualifier = args["Reason qualifier"]
    ? args["Reason qualifier"]
    : null;

  const appLogic = useMockableAppLogic();
  // Replaces, rather than merges, the new warnings over any previous state:
  appLogic.benefitsApplications.warningsLists = {
    [claim.application_id]: warnings ?? [],
  };

  return (
    <Checklist
      appLogic={appLogic}
      claim={claim}
      isLoadingDocuments={args.isLoadingDocuments}
      documents={documents ?? []}
      query={args.query ? { [args.query]: true } : {}}
      user={new User({})}
    />
  );
};

export const BlankApplication = Template.bind({});
export const InProgressStep = Template.bind({});
InProgressStep.args = {
  "Active step(s)": "2. Employment Information - In progress",
};

export const Bonding = Template.bind({});
Bonding.args = {
  "Active step(s)": "8 & 9 - No uploads",
  "Leave reason": LeaveReason.bonding,
  "Reason qualifier": ReasonQualifier.newBorn,
  "Future child birth/placement": false,
};

export const FutureBonding = Template.bind({});
FutureBonding.args = {
  "Active step(s)": "8 & 9 - No uploads",
  "Leave reason": LeaveReason.bonding,
  "Reason qualifier": ReasonQualifier.newBorn,
  "Future child birth/placement": true,
};
