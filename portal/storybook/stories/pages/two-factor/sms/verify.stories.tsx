import { Props } from "types/common";
import React from "react";
import { VerifySMS } from "src/pages/two-factor/sms/verify";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Auth/Two-Factor/SMS/Verify",
  component: VerifySMS,
};

export const Page = (args: Props<typeof VerifySMS>) => {
  const query = { next: "" };
  const appLogic = useMockableAppLogic();
  return <VerifySMS {...args} appLogic={appLogic} query={query} />;
};
