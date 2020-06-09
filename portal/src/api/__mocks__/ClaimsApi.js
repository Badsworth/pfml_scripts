import Claim from "../../../src/models/Claim";
import { uniqueId } from "lodash";

// Export mocked ClaimsApi functions so we can spy on them
// e.g.
// import { createClaimMock } from "./src/api/ClaimsApi";
// expect(createClaimMock).toHaveBeenCalled();
export const createClaimMock = jest.fn(async () =>
  Promise.resolve({
    success: true,
    status: 200,
    apiErrors: null,
    claim: new Claim({
      application_id: `mock-created-claim-application-id-${uniqueId()}`,
    }),
  })
);

export const getClaimsMock = jest.fn(async () =>
  Promise.resolve({
    success: true,
    status: 200,
    apiErrors: null,
    claims: [
      new Claim({ application_id: "mock-application-id-1" }),
      new Claim({ application_id: "mock-application-id-2" }),
    ],
  })
);

export const updateClaimMock = jest.fn(async (application_id, patchData) =>
  Promise.resolve({
    success: true,
    status: 200,
    apiErrors: null,
    claim: new Claim({
      application_id,
      ...patchData,
    }),
  })
);

export const submitClaimMock = jest.fn(async (formState) =>
  Promise.resolve({
    success: true,
    status: 200,
    apiErrors: null,
    claim: new Claim(formState),
  })
);

const claimsApi = jest.fn().mockImplementation(({ user }) => ({
  createClaim: createClaimMock,
  getClaims: getClaimsMock,
  updateClaim: updateClaimMock,
  submitClaim: submitClaimMock,
}));

export default claimsApi;
