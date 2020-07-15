import Claim from "../../models/Claim";
import ClaimCollection from "../../models/ClaimCollection";
import { uniqueId } from "lodash";

export default jest.fn(() => ({
  auth: {
    createAccount: jest.fn(),
    forgotPassword: jest.fn(),
    login: jest.fn(),
    resendVerifyAccountCode: jest.fn(),
    verifyAccount: jest.fn(),
  },
  claims: new ClaimCollection(),
  createClaim: jest.fn(() => new Claim({ application_id: uniqueId() })),
  loadClaims: jest.fn(),
  goToNextPage: jest.fn(),
  setAppErrors: jest.fn(),
  submitClaim: jest.fn(),
  updateClaim: jest.fn(),
}));
