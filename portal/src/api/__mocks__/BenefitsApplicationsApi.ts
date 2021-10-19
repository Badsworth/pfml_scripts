import BenefitsApplication, {
  BenefitsApplicationStatus,
} from "../../models/BenefitsApplication";
import BenefitsApplicationCollection from "../../models/BenefitsApplicationCollection";
import { uniqueId } from "lodash";

// Export mocked BenefitsApplicationsApi functions so we can spy on them
// e.g.
// import { createClaimMock } from "./src/api/BenefitsApplicationsApi";
// expect(createClaimMock).toHaveBeenCalled();

export const completeClaimMock = jest.fn((application_id) =>
  Promise.resolve({
    success: true,
    status: 200,
    claim: new BenefitsApplication({
      application_id,
      status: BenefitsApplicationStatus.completed,
    }),
    warnings: [],
  })
);

export const createClaimMock = jest.fn(() =>
  Promise.resolve({
    success: true,
    status: 201,
    claim: new BenefitsApplication({
      application_id: `mock-created-claim-application-id-${uniqueId()}`,
      status: BenefitsApplicationStatus.started,
    }),
    warnings: [],
  })
);

export const getClaimMockApplicationId = "mock-application-id-1";
export const getClaimMock = jest.fn(() =>
  Promise.resolve({
    success: true,
    status: 200,
    claim: new BenefitsApplication({
      application_id: getClaimMockApplicationId,
      status: BenefitsApplicationStatus.started,
    }),
    warnings: [],
  })
);

export const getClaimsMock = jest.fn(() =>
  Promise.resolve({
    success: true,
    status: 200,
    claims: new BenefitsApplicationCollection([
      new BenefitsApplication({
        application_id: getClaimMockApplicationId,
        status: BenefitsApplicationStatus.started,
      }),
      new BenefitsApplication({
        application_id: "mock-application-id-2",
        status: BenefitsApplicationStatus.started,
      }),
    ]),
    warnings: [],
  })
);

export const updateClaimMock = jest.fn((application_id, patchData) =>
  Promise.resolve({
    success: true,
    status: 200,
    claim: new BenefitsApplication({
      application_id,
      status: BenefitsApplicationStatus.started,
      ...patchData,
    }),
    warnings: [],
  })
);

export const submitClaimMock = jest.fn((application_id) =>
  Promise.resolve({
    success: true,
    status: 201,
    claim: new BenefitsApplication({
      application_id,
      status: BenefitsApplicationStatus.submitted,
    }),
    warnings: [],
  })
);

export const submitPaymentPreferenceMock = jest.fn(
  (application_id, paymentPreferenceData) =>
    Promise.resolve({
      success: true,
      status: 201,
      claim: new BenefitsApplication({
        application_id,
        has_submitted_payment_preference: true,
        payment_preference: paymentPreferenceData,
      }),
      warnings: [],
      errors: [],
    })
);

const claimsApi = jest.fn().mockImplementation(() => ({
  completeClaim: completeClaimMock,
  createClaim: createClaimMock,
  getClaim: getClaimMock,
  getClaims: getClaimsMock,
  updateClaim: updateClaimMock,
  submitClaim: submitClaimMock,
  submitPaymentPreference: submitPaymentPreferenceMock,
}));

export default claimsApi;
