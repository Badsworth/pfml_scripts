import { ConfirmSMS } from "src/pages/two-factor/sms/confirm";
import React from "react";

export default {
  title: "Pages/Auth/Two-Factor/SMS/Confirm",
  component: ConfirmSMS,
};

export const Page = () => {
  const appLogic = {};
  // @ts-expect-error ts-migrate(2740) FIXME: Type '{}' is missing the following properties from... Remove this comment to see the full error message
  return <ConfirmSMS appLogic={appLogic} />;
};

Page.argTypes = {};
