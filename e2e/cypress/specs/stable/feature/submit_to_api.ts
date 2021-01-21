import * as portal from "../../../tests/common/actions/portal";

describe("Direct API Claim Submission", function () {
  it("Should accept a HAP1 submission", () => {
    portal.submitClaimDirectlyToAPI("BHAP1", "financially eligible");
  });
});
