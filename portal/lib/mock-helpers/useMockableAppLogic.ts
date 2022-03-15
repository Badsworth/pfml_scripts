import useAppLogic, { AppLogic } from "../../src/hooks/useAppLogic";
import User from "../../src/models/User";
import createMockFn from "./createMockFn";
import { faker } from "@faker-js/faker";
import { merge } from "lodash";

const authenticateUser = (appLogic: AppLogic) => {
  appLogic.auth.requireLogin = createMockFn(() =>
    Promise.resolve()
  ) as () => Promise<void>;
  appLogic.users.requireUserConsentToDataAgreement = createMockFn();
  appLogic.users.requireUserRole = createMockFn();
  appLogic.users.user = new User({
    auth_id: faker.datatype.uuid(),
    consented_to_data_sharing: true,
    email_address: faker.internet.email(),
    user_id: faker.datatype.uuid(),
  });
};

/**
 * Replace appLogic properties with a mocked version
 * @param mockedLogic - The subset of appLogic to mock
 */
const useMockableAppLogic = (
  mockedLogic: {
    [appLogicKey in keyof AppLogic]?: Partial<AppLogic[appLogicKey]>;
  } = {},
  { isLoggedIn } = { isLoggedIn: true }
): AppLogic => {
  const appLogic = useAppLogic();

  if (isLoggedIn) {
    authenticateUser(appLogic);
  }

  return merge(appLogic, mockedLogic);
};

export default useMockableAppLogic;
