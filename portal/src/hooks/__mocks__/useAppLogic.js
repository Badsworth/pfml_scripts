import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import Claim from "../../models/Claim";
import ClaimCollection from "../../models/ClaimCollection";
import User from "../../models/User";
import { uniqueId } from "lodash";

export default jest.fn(() => ({
  appErrors: new AppErrorInfoCollection(),
  auth: {
    createAccount: jest.fn(),
    forgotPassword: jest.fn(),
    isLoggedIn: true,
    login: jest.fn(),
    requireLogin: jest.fn(),
    resendVerifyAccountCode: jest.fn(),
    verifyAccount: jest.fn(),
  },
  claims: {
    claims: new ClaimCollection(),
    create: jest.fn(() => new Claim({ application_id: uniqueId() })),
    get: jest.fn(),
    load: jest.fn(),
    submit: jest.fn(),
    update: jest.fn(),
  },
  goToNextPage: jest.fn(),
  setAppErrors: jest.fn(),
  updateUser: jest.fn(),
  user: new User({ user_id: "mock_user_id", consented_to_data_sharing: true }),
  users: {
    loadUser: jest.fn(),
    requireUserConsentToDataAgreement: jest.fn(),
    updateUser: jest.fn(),
    user: new User({
      user_id: "mock_user_id",
      consented_to_data_sharing: true,
    }),
  },
}));
