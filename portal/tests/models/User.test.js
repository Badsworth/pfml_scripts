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

const VERIFIED_EMPLOYER_WITH_DATA = new UserLeaveAdministrator({
  employer_dba: "Dunder Mifflin",
  employer_fein: "11-111111",
  employer_id: "123",
  has_verification_data: true,
  verified: true,
});

const VERIFIED_EMPLOYER_WITHOUT_DATA = new UserLeaveAdministrator({
  employer_dba: "Scranton Co.",
  employer_fein: "33-333333",
  employer_id: "678",
  has_verification_data: false,
  verified: true,
});

const UNVERIFIED_EMPLOYER_WITHOUT_DATA = new UserLeaveAdministrator({
  employer_dba: "Somehow I Manage Publishing",
  employer_fein: "44-444444",
  employer_id: "900",
  has_verification_data: false,
  verified: false,
});

const UNVERIFIED_EMPLOYER_WITH_DATA = new UserLeaveAdministrator({
  employer_dba: "A Papier Company",
  employer_fein: "22-222222",
  employer_id: "345",
  has_verification_data: true,
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

  describe("#isVerifiableEmployer", () => {
    const user = new User({});

    it("returns true if employer is not verified and has verification data", () => {
      expect(user.isVerifiableEmployer(UNVERIFIED_EMPLOYER_WITH_DATA)).toBe(
        true
      );
    });

    it("returns false if employer is not verified but does not have verification data", () => {
      expect(user.isVerifiableEmployer(UNVERIFIED_EMPLOYER_WITHOUT_DATA)).toBe(
        false
      );
    });

    it("returns false if employer is verified regardless of whether they have verification data", () => {
      expect(user.isVerifiableEmployer(VERIFIED_EMPLOYER_WITHOUT_DATA)).toBe(
        false
      );
      expect(user.isVerifiableEmployer(VERIFIED_EMPLOYER_WITH_DATA)).toBe(
        false
      );
    });
  });

  describe("#hasVerifiableEmployer", () => {
    it("returns true when the list of employers includes an unverified employer with withholding data", () => {
      const user = new User({
        user_leave_administrators: [
          UNVERIFIED_EMPLOYER_WITH_DATA,
          UNVERIFIED_EMPLOYER_WITHOUT_DATA,
          VERIFIED_EMPLOYER_WITHOUT_DATA,
          VERIFIED_EMPLOYER_WITH_DATA,
        ],
      });

      expect(user.hasVerifiableEmployer).toBe(true);
    });

    it("returns false when the list of employers does not include an unverified employer with withholding data", () => {
      const user = new User({
        user_leave_administrators: [
          UNVERIFIED_EMPLOYER_WITHOUT_DATA,
          VERIFIED_EMPLOYER_WITHOUT_DATA,
          VERIFIED_EMPLOYER_WITH_DATA,
        ],
      });

      expect(user.hasVerifiableEmployer).toBe(false);
    });

    it("returns false when there are no employers", () => {
      const userWithoutEmployer = new User({
        user_leave_administrators: [],
      });

      expect(userWithoutEmployer.hasVerifiableEmployer).toBe(false);
    });
  });

  describe("#getVerifiableEmployerById", () => {
    it("returns verifiable employer", () => {
      const user = new User({
        user_leave_administrators: [
          UNVERIFIED_EMPLOYER_WITH_DATA,
          UNVERIFIED_EMPLOYER_WITHOUT_DATA,
          VERIFIED_EMPLOYER_WITHOUT_DATA,
          VERIFIED_EMPLOYER_WITH_DATA,
        ],
      });

      expect(user.getVerifiableEmployerById("345")).toEqual(
        UNVERIFIED_EMPLOYER_WITH_DATA
      );
    });

    it("returns undefined if employer id does not match", () => {
      const user = new User({
        user_leave_administrators: [
          UNVERIFIED_EMPLOYER_WITH_DATA,
          UNVERIFIED_EMPLOYER_WITHOUT_DATA,
          VERIFIED_EMPLOYER_WITHOUT_DATA,
          VERIFIED_EMPLOYER_WITH_DATA,
        ],
      });

      expect(user.getVerifiableEmployerById("100")).toEqual(undefined);
    });

    it("returns undefined if employer is unverified but does not have verification data", () => {
      const user = new User({
        user_leave_administrators: [
          UNVERIFIED_EMPLOYER_WITHOUT_DATA,
          VERIFIED_EMPLOYER_WITHOUT_DATA,
          VERIFIED_EMPLOYER_WITH_DATA,
        ],
      });

      expect(user.getVerifiableEmployerById("900")).toEqual(undefined);
    });
  });
});
