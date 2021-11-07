import React from "react";
import { SetupSMS } from "src/pages/two-factor/sms/index";

export default {
  title: "Pages/Auth/Two-Factor/SMS/Index",
  component: SetupSMS,
};

export const Page = () => {
  const appLogic = {};
  // @ts-expect-error ts-migrate(2740) FIXME: Type '{}' is missing the following properties from... Remove this comment to see the full error message
  return <SetupSMS appLogic={appLogic} />;
};

Page.argTypes = {};
