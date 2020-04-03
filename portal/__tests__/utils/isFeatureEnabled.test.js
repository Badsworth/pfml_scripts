import isFeatureEnabled from "../../src/utils/isFeatureEnabled";

describe("isFeatureEnabled", () => {
  beforeEach(() => {
    // Reset the feature flags
    process.env = {
      ...process.env,
      featureFlags: {},
    };
  });

  it("returns undefined if a flag isn't found", () => {
    expect(isFeatureEnabled("undefinedFeature")).toBeUndefined();
  });

  describe("when a flag is only defined at the environment level", () => {
    it("returns the value of the feature flag defined in the environment variables", () => {
      process.env = {
        ...process.env,
        featureFlags: {
          featureA: true,
          featureB: false,
        },
      };

      expect(isFeatureEnabled("featureA")).toBe(true);
      expect(isFeatureEnabled("featureB")).toBe(false);
    });
  });

  describe("when a flag is overridden in a cookie", () => {
    // https://lwd.atlassian.net/browse/CP-28
    it.todo("returns the value of the feature flag defined in the cookie");
  });
});
