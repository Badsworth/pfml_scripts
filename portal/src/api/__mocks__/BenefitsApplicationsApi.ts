import BenefitsApplication, {
  BenefitsApplicationStatus,
} from "../../models/BenefitsApplication";
import BenefitsApplicationCollection from "../../models/BenefitsApplicationCollection";
import { uniqueId } from "lodash";

// Export mocked BenefitsApplicationsApi functions so we can spy on them
// e.g.
// import { createClaimMock } from "./src/api/BenefitsApplicationsApi";
// expect(createClaimMock).toHaveBeenCalled();

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
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

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
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
// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
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

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
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

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
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

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
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

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
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

// @ts-expect-error ts-migrate(2304) FIXME: Cannot find name 'jest'.
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
