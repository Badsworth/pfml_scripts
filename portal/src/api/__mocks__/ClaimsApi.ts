import ApiResourceCollection from "../../models/ApiResourceCollection";
import Claim from "../../models/Claim";
import createMockClaim from "../../../lib/mock-helpers/createMockClaim";

// Export mocked ClaimsApi functions so we can spy on them
// e.g.
// import { getClaimsMock } from "./src/api/ClaimsApi";
// expect(getClaimsMock).toHaveBeenCalled();

export const getClaimsMock = jest.fn().mockResolvedValue({
  claims: new ApiResourceCollection<Claim>("fineos_absence_id", [
    createMockClaim({}),
  ]),
  paginationMeta: {
    page_offset: 1,
    page_size: 25,
    total_pages: 1,
    total_records: 1,
    order_by: "created_at",
    order_direction: "ascending",
  },
});

const claimsApi = jest.fn().mockImplementation(() => ({
  getClaims: getClaimsMock,
}));

export default claimsApi;
