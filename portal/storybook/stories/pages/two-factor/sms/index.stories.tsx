import { IndexSMS } from "src/pages/two-factor/sms/index";
import React from "react";
import User from "src/models/User";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Auth/Two-Factor/SMS/Index",
  component: IndexSMS,
};

export const Page = () => {
  const appLogic = useMockableAppLogic();
  return <IndexSMS appLogic={appLogic} user={new User({})} />;
};
