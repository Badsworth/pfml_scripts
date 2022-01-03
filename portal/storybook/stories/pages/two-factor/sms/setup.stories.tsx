import React from "react";
import { SetupSMS } from "src/pages/two-factor/sms/setup";
import User from "src/models/User";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Auth/Two-Factor/SMS/Setup",
  component: SetupSMS,
};

export const Page = () => {
  const appLogic = useMockableAppLogic();
  return <SetupSMS appLogic={appLogic} user={new User({})} query={{}} />;
};
