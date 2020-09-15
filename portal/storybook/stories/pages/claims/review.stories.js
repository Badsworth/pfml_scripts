import { MockClaimBuilder } from "tests/test-utils";
import generateClaimPageStory from "storybook/utils/generateClaimPageStory";

const mockClaims = {
  complete: new MockClaimBuilder().complete().create(),
  debit: new MockClaimBuilder().complete().debit().create(),
};

const { config, DefaultStory } = generateClaimPageStory("review", mockClaims);
export default config;
export const Default = DefaultStory;
