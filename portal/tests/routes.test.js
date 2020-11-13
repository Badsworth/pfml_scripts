import routes, { isClaimsRoute, isEmployersRoute } from "../src/routes";

describe("routes", () => {
  const claimsRoute = `${routes.claims.stateId}?claim_id=123`;
  const employersRoute = `${routes.employers.review}/?absence_id=123`;
  const fakeClaimsRoute = "/claims/test-page";
  const fakeEmployersRoute = "/employers/test-page";
  const rootRoute = "/";

  describe("isEmployersRoute", () => {
    it("returns true if route is in Employer Portal", () => {
      expect(isEmployersRoute(employersRoute)).toEqual(true);
    });

    it("returns false if route is not in Employer Portal", () => {
      expect(isEmployersRoute(claimsRoute)).toEqual(false);
      expect(isEmployersRoute(fakeEmployersRoute)).toEqual(false);
      expect(isEmployersRoute(rootRoute)).toEqual(false);
      expect(isEmployersRoute("")).toEqual(false);
    });
  });

  describe("isClaimsRoute", () => {
    it("returns true if route is in Claimant Portal", () => {
      expect(isClaimsRoute(claimsRoute)).toEqual(true);
      expect(isClaimsRoute("/dashboard")).toEqual(true);
    });

    it("returns false if route is not in Claimant Portal", () => {
      expect(isClaimsRoute(employersRoute)).toEqual(false);
      expect(isClaimsRoute(fakeClaimsRoute)).toEqual(false);
      expect(isClaimsRoute(rootRoute)).toEqual(false);
      expect(isClaimsRoute("")).toEqual(false);
    });
  });
});
