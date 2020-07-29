import Claim, { ClaimStatus } from "../../src/models/Claim";
import ClaimCollection from "../../src/models/ClaimCollection";

describe("ClaimCollection", () => {
  let collection, completedClaim, inProgressClaim, submittedClaim;

  beforeEach(() => {
    inProgressClaim = new Claim({
      application_id: "1",
      status: ClaimStatus.started,
    });
    completedClaim = new Claim({
      application_id: "2",
      status: ClaimStatus.completed,
    });
    submittedClaim = new Claim({
      application_id: "3",
      status: ClaimStatus.submitted,
    });
    collection = new ClaimCollection([
      inProgressClaim,
      completedClaim,
      submittedClaim,
    ]);
  });

  describe("#inProgress", () => {
    it("returns only the 'Started' claims", () => {
      expect(collection.inProgress).toHaveLength(1);
      expect(collection.inProgress).toEqual([inProgressClaim]);
    });
  });

  describe("#submitted", () => {
    it("returns 'Completed' and 'Submitted' claims", () => {
      expect(collection.submitted).toHaveLength(2);
      expect(collection.submitted).toContain(completedClaim);
      expect(collection.submitted).toContain(submittedClaim);
    });
  });
});
