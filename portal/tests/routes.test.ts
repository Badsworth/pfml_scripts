import routes, { isApplicationsRoute, isEmployersRoute } from "../src/routes";

describe("routes", () => {
  const claimsRoute = `${routes.applications.stateId}?claim_id=123`;
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

  describe("isApplicationsRoute", () => {
    it("returns true if route is in Claimant Portal", () => {
      expect(isApplicationsRoute(claimsRoute)).toEqual(true);
      expect(isApplicationsRoute("/applications/get-ready")).toEqual(true);
    });

    it("returns false if route is not in Claimant Portal", () => {
      expect(isApplicationsRoute(employersRoute)).toEqual(false);
      expect(isApplicationsRoute(fakeClaimsRoute)).toEqual(false);
      expect(isApplicationsRoute(rootRoute)).toEqual(false);
      expect(isApplicationsRoute("")).toEqual(false);
    });
  });
});
