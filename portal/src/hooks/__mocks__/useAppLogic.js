import Claim from "../../models/Claim";
import ClaimCollection from "../../models/ClaimCollection";
import { uniqueId } from "lodash";

export default jest.fn(() => ({
  claims: new ClaimCollection(),
  loadClaims: jest.fn(),
  login: jest.fn(),
  createClaim: jest.fn(() => new Claim({ application_id: uniqueId() })),
  updateClaim: jest.fn(),
  submitClaim: jest.fn(),
}));
