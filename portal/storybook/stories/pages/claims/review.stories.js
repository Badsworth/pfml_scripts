import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  bondingAdoptionLeave: new MockClaimBuilder()
    .complete()
    .bondingAdoptionLeaveReason()
    .create(),
  bondingBirthLeave: new MockClaimBuilder()
    .complete()
    .bondingBirthLeaveReason()
    .create(),
  bondingFosterCareLeave: new MockClaimBuilder()
    .complete()
    .bondingFosterCareLeaveReason()
    .create(),
  complete: new MockClaimBuilder().complete().create(),
  debit: new MockClaimBuilder().complete().debit().create(),
};

const { config, DefaultStory } = generateClaimPageStory("review", mockClaims);
export default config;
export const Default = DefaultStory;
