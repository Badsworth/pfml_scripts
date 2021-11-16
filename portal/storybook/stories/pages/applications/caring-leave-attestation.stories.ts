import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  Child: new MockBenefitsApplicationBuilder()
    .caringLeaveReason({ relationship_to_caregiver: "Child" })
    .create(),
  Grandchild: new MockBenefitsApplicationBuilder()
    .caringLeaveReason({ relationship_to_caregiver: "Grandchild" })
    .create(),
  Grandparent: new MockBenefitsApplicationBuilder()
    .caringLeaveReason({ relationship_to_caregiver: "Grandparent" })
    .create(),
  Inlaw: new MockBenefitsApplicationBuilder()
    .caringLeaveReason({ relationship_to_caregiver: "Inlaw" })
    .create(),
  Parent: new MockBenefitsApplicationBuilder()
    .caringLeaveReason({ relationship_to_caregiver: "Parent" })
    .create(),
  "Sibling - Brother/Sister": new MockBenefitsApplicationBuilder()
    .caringLeaveReason({
      relationship_to_caregiver: "Sibling - Brother/Sister",
    })
    .create(),
  Spouse: new MockBenefitsApplicationBuilder()
    .caringLeaveReason({ relationship_to_caregiver: "Spouse" })
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "caring-leave-attestation",
  // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '{ Child: BenefitsApplication; Gr... Remove this comment to see the full error message
  mockClaims
);
export default config;
export const Default = DefaultStory;
