import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  Child: new MockClaimBuilder()
    .caringLeaveReason({ relationship_to_caregiver: "Child" })
    .create(),
  Grandchild: new MockClaimBuilder()
    .caringLeaveReason({ relationship_to_caregiver: "Grandchild" })
    .create(),
  Grandparent: new MockClaimBuilder()
    .caringLeaveReason({ relationship_to_caregiver: "Grandparent" })
    .create(),
  Inlaw: new MockClaimBuilder()
    .caringLeaveReason({ relationship_to_caregiver: "Inlaw" })
    .create(),
  Parent: new MockClaimBuilder()
    .caringLeaveReason({ relationship_to_caregiver: "Parent" })
    .create(),
  "Sibling - Brother/Sister": new MockClaimBuilder()
    .caringLeaveReason({
      relationship_to_caregiver: "Sibling - Brother/Sister",
    })
    .create(),
  Spouse: new MockClaimBuilder()
    .caringLeaveReason({ relationship_to_caregiver: "Spouse" })
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "caring-leave-attestation",
  mockClaims
);
export default config;
export const Default = DefaultStory;
