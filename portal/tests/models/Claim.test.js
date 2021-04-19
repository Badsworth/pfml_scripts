import Claim, { ClaimEmployee, ClaimEmployer } from "../../src/models/Claim";

describe("Claim", () => {
  /* eslint-disable no-new */
  it("logs error when employee and employer are plain objects", () => {
    const errorSpy = jest.spyOn(console, "error").mockImplementation(jest.fn());

    // null is fine
    new Claim({
      employee: null,
      employer: null,
    });
    expect(errorSpy).toHaveBeenCalledTimes(0);

    // instances are fine
    new Claim({
      employee: new ClaimEmployee({ first_name: "Bud" }),
      employer: new ClaimEmployer({ employer_fein: "12-3456789" }),
    });
    expect(errorSpy).toHaveBeenCalledTimes(0);

    // objects are not okay
    new Claim({
      employee: { first_name: "Bud" },
      employer: { employer_fein: "12-3456789" },
    });
    expect(errorSpy).toHaveBeenCalledTimes(2);
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
