import {
  isFeatureEnabled,
  storeFeatureFlagsFromQuery,
} from "../../src/services/featureFlags";
import Cookies from "js-cookie";
import tracker from "../../src/services/tracker";

jest.mock("../../src/services/tracker");

describe("isFeatureEnabled", () => {
  afterEach(() => {
    Cookies.remove("_ff");
  });

  it("returns undefined if a flag isn't found", () => {
    expect(isFeatureEnabled("undefinedFeature")).toBeUndefined();
  });

  describe("when a flag is only defined at the environment level", () => {
    it("returns the value of the feature flag defined in the environment variables", () => {
      process.env.featureFlags = JSON.stringify({
        featureA: true,
        featureB: false,
      });

      expect(isFeatureEnabled("featureA")).toBe(true);
      expect(isFeatureEnabled("featureB")).toBe(false);
    });
  });

  describe("when a flag is overridden in a cookie", () => {
    it("returns the value of the feature flag defined in the cookie", () => {
      process.env.featureFlags = JSON.stringify({
        featureA: true,
        featureB: false,
      });

      Cookies.set(
        "_ff",
        JSON.stringify({
          featureA: false,
        })
      );

      expect(isFeatureEnabled("featureA")).toBe(false);
    });
  });
});

describe("storeFeatureFlagsFromQuery", () => {
  const cookiesSet = jest.spyOn(Cookies, "set");

  afterEach(() => {
    cookiesSet.mockClear();
    Cookies.remove("_ff");
  });

  describe("when the URL doesn't include a query string", () => {
    it("doesn't set a Cookie", () => {
      storeFeatureFlagsFromQuery(new URLSearchParams());

      expect(cookiesSet).not.toHaveBeenCalled();
    });

    it("doesn't track an event", () => {
      storeFeatureFlagsFromQuery(new URLSearchParams());

      expect(tracker.trackEvent).not.toHaveBeenCalled();
    });
  });

  describe("when the URL includes a non-feature-flag query string", () => {
    it("doesn't set a Cookie", () => {
      const searchParams = new URLSearchParams("claimId=123");
      storeFeatureFlagsFromQuery(searchParams);

      expect(cookiesSet).not.toHaveBeenCalled();
    });
  });

  describe("when the URL includes the feature flag query string", () => {
    it("adds the flags in the querystring to the cookie", () => {
      process.env.featureFlags = JSON.stringify({ flagA: false, flagB: true });
      const searchParams = new URLSearchParams("_ff=flagA:true;flagB:false");

      storeFeatureFlagsFromQuery(searchParams);

      expect(cookiesSet).toHaveBeenLastCalledWith(
        "_ff",
        JSON.stringify({
          flagA: true,
          flagB: false,
        }),
        { expires: 180 }
      );
    });

    it("does not include a flag in the cookie if the flag doesn't exist at the environment-level", () => {
      jest.spyOn(console, "warn").mockImplementationOnce(jest.fn());
      process.env.featureFlags = JSON.stringify({ flagA: true });
      const searchParams = new URLSearchParams(
        "_ff=flagA:true;unknownFlag:true"
      );

      storeFeatureFlagsFromQuery(searchParams);

      expect(cookiesSet).toHaveBeenLastCalledWith(
        "_ff",
        JSON.stringify({
          flagA: true,
        }),
        { expires: 180 }
      );
    });

    it("does not include a flag in the cookie when its value is 'reset'", () => {
      process.env.featureFlags = JSON.stringify({ flagC: true, flagD: false });
      const searchParams = new URLSearchParams("_ff=flagC:reset;flagD:true");

      storeFeatureFlagsFromQuery(searchParams);

      expect(cookiesSet).toHaveBeenCalledWith(
        "_ff",
        JSON.stringify({
          flagD: true,
        }),
        expect.anything()
      );
    });

    it("tracks an event", () => {
      process.env.featureFlags = JSON.stringify({ flagA: false, flagB: true });
      const searchParams = new URLSearchParams("_ff=flagA:true");

      storeFeatureFlagsFromQuery(searchParams);

      expect(tracker.trackEvent).toHaveBeenCalledWith("manual_feature_flags", {
        flags: '[["flagA","true"]]',
      });
    });
  });

  describe("when the URL includes a feature flag query string param and some other unrelated param", () => {
    it("adds the flags to the cookie, and isn't affected by the other query string param", () => {
      process.env.featureFlags = JSON.stringify({ flagA: false });
      const searchParams = new URLSearchParams(
        "_ff=flagA:true&anotherParam=123"
      );

      storeFeatureFlagsFromQuery(searchParams);

      expect(cookiesSet).toHaveBeenLastCalledWith(
        "_ff",
        JSON.stringify({
          flagA: true,
        }),
        { expires: 180 }
      );
    });
  });
});
