import { ConfirmSMS } from "src/pages/two-factor/sms/confirm";
import React from "react";
import User from "src/models/User";

import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Auth/Two-Factor/SMS/Confirm",
  component: ConfirmSMS,
};

export const Page = () => {
  const appLogic = useMockableAppLogic();
  const user = new User({ mfa_phone_number: "123-456-7891" });
  return <ConfirmSMS appLogic={appLogic} user={user} />;
};
