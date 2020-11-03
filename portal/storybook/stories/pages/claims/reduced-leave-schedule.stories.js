import { MockClaimBuilder } from "tests/test-utils";
import { WorkPattern } from "src/models/Claim";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

// 8 hours days for 7 days
const defaultMinutesWorked = 8 * 60 * 7;
const workPattern = WorkPattern.addWeek(
  new WorkPattern(),
  defaultMinutesWorked
);

const mockClaims = {
  bonding: new MockClaimBuilder()
    .workPattern(workPattern)
    .bondingBirthLeaveReason()
    .create(),
  medical: new MockClaimBuilder()
    .workPattern(workPattern)
    .medicalLeaveReason()
    .create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "reduced-leave-schedule",
  mockClaims
);
export default config;
export const Default = DefaultStory;
