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
    warnings: [],
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
    warnings: [],
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
    warnings: [],
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
    warnings: [],
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
    warnings: [],
  })
);

export const submitPaymentPreferenceMock = jest.fn(
  (application_id, paymentPreferenceData) =>
    Promise.resolve({
      success: true,
      status: 201,
      claim: new Claim({
        application_id,
        has_submitted_payment_preference: true,
        payment_preference: paymentPreferenceData,
      }),
      warnings: [],
      errors: [],
    })
);

const claimsApi = jest.fn().mockImplementation(({ user }) => ({
  completeClaim: completeClaimMock,
  createClaim: createClaimMock,
  getClaim: getClaimMock,
  getClaims: getClaimsMock,
  updateClaim: updateClaimMock,
  submitClaim: submitClaimMock,
  submitPaymentPreference: submitPaymentPreferenceMock,
}));

export default claimsApi;
