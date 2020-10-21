import Claim, { ClaimStatus } from "../../models/Claim";
import ClaimCollection from "../../models/ClaimCollection";
import { uniqueId } from "lodash";

// Export mocked ClaimsApi functions so we can spy on them
// e.g.
// import { createClaimMock } from "./src/api/ClaimsApi";
// expect(createClaimMock).toHaveBeenCalled();

export const completeClaimMock = jest.fn((application_id) =>
  Promise.resolve({
    success: true,
    status: 200,
    claim: new Claim({
      application_id,
      status: ClaimStatus.completed,
    }),
  })
);

export const createClaimMock = jest.fn(() =>
  Promise.resolve({
    success: true,
    status: 201,
    claim: new Claim({
      application_id: `mock-created-claim-application-id-${uniqueId()}`,
      status: ClaimStatus.started,
    }),
  })
);

export const getClaimMockApplicationId = "mock-application-id-1";
export const getClaimMock = jest.fn(() =>
  Promise.resolve({
    success: true,
    status: 200,
    claim: new Claim({
      application_id: getClaimMockApplicationId,
      status: ClaimStatus.started,
    }),
    warnings: [],
  })
);

export const getClaimsMock = jest.fn(() =>
  Promise.resolve({
    success: true,
    status: 200,
    claims: new ClaimCollection([
      new Claim({
        application_id: getClaimMockApplicationId,
        status: ClaimStatus.started,
      }),
      new Claim({
        application_id: "mock-application-id-2",
        status: ClaimStatus.started,
      }),
    ]),
  })
);

export const updateClaimMock = jest.fn((application_id, patchData) =>
  Promise.resolve({
    success: true,
    status: 200,
    claim: new Claim({
      application_id,
      status: ClaimStatus.started,
      ...patchData,
    }),
  })
);

export const submitClaimMock = jest.fn((application_id) =>
  Promise.resolve({
    success: true,
    status: 201,
    claim: new Claim({
      application_id,
      status: ClaimStatus.submitted,
    }),
  })
);

const claimsApi = jest.fn().mockImplementation(({ user }) => ({
  completeClaim: completeClaimMock,
  createClaim: createClaimMock,
  getClaim: getClaimMock,
  getClaims: getClaimsMock,
  updateClaim: updateClaimMock,
  submitClaim: submitClaimMock,
}));

export default claimsApi;
