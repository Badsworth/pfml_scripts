import { storeFeatureFlagsFromQuery } from "../../src/services/featureFlags";
import { testHook } from "../test-utils";
import useFeatureFlagsFromQueryEffect from "../../src/hooks/useFeatureFlagsFromQueryEffect";

jest.mock("../../src/services/featureFlags");

describe("useFeatureFlagsFromQueryEffect", () => {
  const originalLocation = window.location;
  const queryString = "?paramA=foo&paramB=bar";

  beforeEach(() => {
    delete window.location;
    window.location = { search: queryString };
  });

  afterEach(() => {
    window.location = originalLocation;
  });

  it("calls storeFeatureFlagsFromQuery with the query string params", () => {
    testHook(() => {
      useFeatureFlagsFromQueryEffect();
    });

    expect(storeFeatureFlagsFromQuery).toHaveBeenCalledWith(
      new URLSearchParams(queryString)
    );
  });
});
