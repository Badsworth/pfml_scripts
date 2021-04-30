import { portal } from "../../actions";

describe("Direct API Claim Submission", function () {
  it("Should accept a HAP1 submission", () => {
    portal.submitClaimDirectlyToAPI("BHAP1");
  });
});
