import User, {
  RoleDescription,
  UserLeaveAdministrator,
  UserRole,
} from "../../src/models/User";

const EMPLOYER_ROLE = new UserRole({
  role_id: "3mpl0y3r",
  role_description: RoleDescription.employer,
});

const CLAIMANT_ROLE = new UserRole({
  role_id: "cl41m4nt",
});

const VERIFIED_EMPLOYER = new UserLeaveAdministrator({
  employer_dba: "Dunder Mifflin",
  employer_fein: "11-111111",
  employer_id: "123",
  verified: true,
});

const UNVERIFIED_EMPLOYER = new UserLeaveAdministrator({
  employer_dba: "A Papier Company",
  employer_fein: "22-222222",
  employer_id: "345",
  verified: false,
});

describe("User", () => {
  describe("#hasEmployerRole", () => {
    it("returns true when the list of roles includes an employer role", () => {
      const userWithEmployer = new User({
        roles: [EMPLOYER_ROLE, CLAIMANT_ROLE],
      });

      expect(userWithEmployer.hasEmployerRole).toBe(true);
    });

    it("returns false when the list of roles does not include an employer role", () => {
      const userWithoutEmployer = new User({
        roles: [CLAIMANT_ROLE],
      });

      expect(userWithoutEmployer.hasEmployerRole).toBe(false);
    });
  });

  describe("#hasUnverifiedEmployer", () => {
    it("returns true when the list of employers includes an unverified employer", () => {
      const userWithUnverifiedEmployer = new User({
        user_leave_administrators: [VERIFIED_EMPLOYER, UNVERIFIED_EMPLOYER],
      });

      expect(userWithUnverifiedEmployer.hasUnverifiedEmployer).toBe(true);
    });

    it("returns false when the list of employers does not include an unverified employer", () => {
      const userWithVerifiedEmployer = new User({
        user_leave_administrators: [VERIFIED_EMPLOYER],
      });

      expect(userWithVerifiedEmployer.hasUnverifiedEmployer).toBe(false);
    });

    it("returns false when there are no employers", () => {
      const userWithoutEmployer = new User({
        user_leave_administrators: [],
      });

      expect(userWithoutEmployer.hasUnverifiedEmployer).toBe(false);
    });
  });
});
