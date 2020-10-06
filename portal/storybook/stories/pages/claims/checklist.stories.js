import { DateTime } from "luxon";
import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const futureBirthDate = DateTime.local.plus({ days: 60 }).toISODate();

const mockClaims = {
  empty: new MockClaimBuilder().create(),
  "verified id": new MockClaimBuilder().verifiedId().create(),
  "medical leave": new MockClaimBuilder()
    .verifiedId()
    .medicalLeaveReason()
    .create(),
  "Part 1 ready for submit": new MockClaimBuilder()
    .verifiedId()
    .medicalLeaveReason()
    .employed()
    .noOtherLeave()
    .create(),
  "Future bonding leave": new MockClaimBuilder()
    .bondingBirthLeaveReason(futureBirthDate)
    .submitted()
    .create(),
  submitted: new MockClaimBuilder().submitted().create(),
  complete: new MockClaimBuilder().complete().create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "checklist",
  mockClaims
);
export default config;
export const Default = DefaultStory;
