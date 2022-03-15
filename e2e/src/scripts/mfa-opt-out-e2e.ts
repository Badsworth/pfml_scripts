import config from "../config";
import AuthenticationManager from "../submission/AuthenticationManager";
import { getUsersCurrent, patchUsersByUser_id, RequestOptions } from "../_api";
import { Credentials } from "../types";

/* This script is used to opt out of MFA, primarily after db refreshes. 
   If you have a portal account that is used for regular E2E activities and you want MFA disabled, you can add those credentials to this script
*/
(async () => {
  // Accounts used for regular E2E activity
  const users: Credentials[] = [
    {
      username: config("PORTAL_USERNAME"),
      password: config("PORTAL_PASSWORD"),
    },
    {
      username: "armando+payment_status@lastcallmedia.com",
      password: config("PORTAL_PASSWORD"),
    },
  ];
  const authenticator = AuthenticationManager.create(config);

  // callback to authenticate and opt out of MFA directly through API
  const optOut = async ({ username, password }: Credentials) => {
    const session = await authenticator.authenticate(username, password);
    const opts: RequestOptions = {
      baseUrl: config("API_BASEURL"),
      headers: {
        Authorization: `Bearer ${session.getAccessToken().getJwtToken()}`,
        "User-Agent": "PFML Business Simulation Bot",
      },
    };
    const { data } = await getUsersCurrent(opts);
    if (!data.data.user_id) throw Error("user_id undefined");
    await patchUsersByUser_id(
      { user_id: data.data.user_id },
      {
        mfa_delivery_preference: "Opt Out",
        mfa_phone_number: undefined,
        consented_to_data_sharing: true,
      },
      opts
    );
  };
  users.forEach(optOut);
})();
