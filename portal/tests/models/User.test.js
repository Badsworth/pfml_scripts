import User, { RoleDescription, UserRole } from "../../src/models/User";

const EMPLOYER_ROLE = new UserRole({
  role_id: "3mpl0y3r",
  role_description: RoleDescription.employer,
});

const CLAIMANT_ROLE = new UserRole({
  role_id: "cl41m4nt",
});

describe("User", () => {
  describe("#hasEmployerRole", () => {
    it("returns true when the roles include an employer role", () => {
      const userWithEmployer = new User({
        roles: [EMPLOYER_ROLE, CLAIMANT_ROLE],
      });

      expect(userWithEmployer.hasEmployerRole).toBe(true);
    });

    it("returns false when the roles do not include an employer role", () => {
      const userWithoutEmployer = new User({
        roles: [CLAIMANT_ROLE],
      });

      expect(userWithoutEmployer.hasEmployerRole).toBe(false);
    });
  });
});
