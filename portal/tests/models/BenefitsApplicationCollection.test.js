import BenefitsApplicationCollection from "../../src/models/BenefitsApplicationCollection";
import { MockBenefitsApplicationBuilder } from "../test-utils";

describe("BenefitsApplicationCollection", () => {
  let collection, completedClaim, startedClaim, submittedClaim;

  beforeEach(() => {
    startedClaim = new MockBenefitsApplicationBuilder().create();
    completedClaim = new MockBenefitsApplicationBuilder().completed().create();
    submittedClaim = new MockBenefitsApplicationBuilder().submitted().create();
    collection = new BenefitsApplicationCollection([
      startedClaim,
      completedClaim,
      submittedClaim,
    ]);
  });

  describe("#inProgress", () => {
    it("returns only the 'Started' and 'Submitted' claims", () => {
      expect(collection.inProgress).toHaveLength(2);
      expect(collection.inProgress).toContain(startedClaim);
      expect(collection.inProgress).toContain(submittedClaim);
    });
  });

  describe("#submitted", () => {
    it("returns 'Completed' and 'Submitted' claims", () => {
      expect(collection.submitted).toHaveLength(1);
      expect(collection.submitted).toEqual([submittedClaim]);
    });
  });

  describe("#completed", () => {
    it("returns 'Completed' claims", () => {
      expect(collection.completed).toHaveLength(1);
      expect(collection.completed).toEqual([completedClaim]);
    });
  });
});
