import { MockBenefitsApplicationBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  "state id": new MockBenefitsApplicationBuilder().hasStateId().create(),
  "other id": new MockBenefitsApplicationBuilder().hasOtherId().create(),
};

const { config, DefaultStory } = generateClaimPageStory(
  "upload-id",
  // @ts-expect-error ts-migrate(2345) FIXME: Argument of type '{ "state id": BenefitsApplicatio... Remove this comment to see the full error message
  mockClaims
);
export default config;
export const Default = DefaultStory;
