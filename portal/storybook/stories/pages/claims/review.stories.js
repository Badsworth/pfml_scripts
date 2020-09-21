import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  "Part 1 (Medical)": new MockClaimBuilder().part1Complete().create(),
  "Part 1 (Adoption)": new MockClaimBuilder()
    .part1Complete()
    .bondingAdoptionLeaveReason()
    .create(),
  "Part 1 (Newborn)": new MockClaimBuilder()
    .part1Complete()
    .bondingBirthLeaveReason()
    .create(),
  "Part 1 (Foster care)": new MockClaimBuilder()
    .part1Complete()
    .bondingFosterCareLeaveReason()
    .create(),
  "Final (Deposit)": new MockClaimBuilder().complete().create(),
  "Final (Debit)": new MockClaimBuilder().complete().debit().create(),
};

const { config, DefaultStory } = generateClaimPageStory("review", mockClaims);
export default config;
export const Default = DefaultStory;
