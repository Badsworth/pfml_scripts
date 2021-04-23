import Claim, { ClaimEmployee, ClaimEmployer } from "../../src/models/Claim";

describe("Claim", () => {
  it("instantiates employee and employer models", () => {
    let claim;

    // null is fine
    claim = new Claim({
      employee: null,
      employer: null,
    });
    expect(claim.employee).toBeNull();
    expect(claim.employer).toBeNull();

    // instances are fine
    claim = new Claim({
      employee: new ClaimEmployee({ first_name: "Bud" }),
      employer: new ClaimEmployer({ employer_fein: "12-3456789" }),
    });
    expect(claim.employee).toBeInstanceOf(ClaimEmployee);
    expect(claim.employee.first_name).toBe("Bud");
    expect(claim.employer).toBeInstanceOf(ClaimEmployer);
    expect(claim.employer.employer_fein).toBe("12-3456789");

    // objects get turned into instance
    claim = new Claim({
      employee: { first_name: "Baxter" },
      employer: { employer_fein: "00-3456789" },
    });
    expect(claim.employee).toBeInstanceOf(ClaimEmployee);
    expect(claim.employee.first_name).toBe("Baxter");
    expect(claim.employer).toBeInstanceOf(ClaimEmployer);
    expect(claim.employer.employer_fein).toBe("00-3456789");
  });
});
/* eslint-enable no-new */

describe("ClaimEmployee", () => {
  describe("#fullName", () => {
    it("returns employee's full name", () => {
      const claimWithNoMiddleName = new Claim({
        employee: new ClaimEmployee({
          first_name: "Michael",
          middle_name: null,
          last_name: "Scott",
        }),
      });
      const claimWithMiddleName = new Claim({
        employee: new ClaimEmployee({
          first_name: "Michael",
          middle_name: "Gary",
          last_name: "Scott",
        }),
      });

      expect(claimWithNoMiddleName.employee.fullName).toEqual("Michael Scott");
      expect(claimWithMiddleName.employee.fullName).toEqual(
        "Michael Gary Scott"
      );
    });
  });
});
