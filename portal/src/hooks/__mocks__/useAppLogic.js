import Claim from "../../models/Claim";
import ClaimCollection from "../../models/ClaimCollection";
import { uniqueId } from "lodash";

export default jest.fn(() => ({
  auth: {
    createAccount: jest.fn(),
    forgotPassword: jest.fn(),
    login: jest.fn(),
  },
  claims: new ClaimCollection(),
  createClaim: jest.fn(() => new Claim({ application_id: uniqueId() })),
  loadClaims: jest.fn(),
  submitClaim: jest.fn(),
  updateClaim: jest.fn(),
}));
