import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  "Part 1 (Medical - Continuous)": new MockClaimBuilder()
    .part1Complete({ excludeLeavePeriod: true })
    .continuous()
    .fixedWorkPattern()
    .create(),
  "Part 1 (Medical - Reduced Schedule)": new MockClaimBuilder()
    .part1Complete({ excludeLeavePeriod: true })
    .reducedSchedule()
    .fixedWorkPattern()
    .create(),
  "Part 1 (Adoption - Intermittent)": new MockClaimBuilder()
    .part1Complete({ excludeLeavePeriod: true })
    .bondingAdoptionLeaveReason()
    .variableWorkPattern()
    .intermittent()
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
  "Final (Paper check)": new MockClaimBuilder().complete().check().create(),
};

const { config, DefaultStory } = generateClaimPageStory("review", mockClaims);
export default config;
export const Default = DefaultStory;
