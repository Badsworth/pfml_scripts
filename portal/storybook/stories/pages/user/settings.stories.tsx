import { Props } from "storybook/types";
import React from "react";
import { Settings } from "src/pages/user/settings";
import User from "src/models/User";
import routes from "src/routes";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/User/Settings",
  component: Settings,
  argTypes: {
    mfaEnabled: {
      control: {
        type: "boolean",
      },
    },
  },
};

export const Page = (
  args: Props<typeof Settings> & { mfaEnabled: boolean }
) => {
  const user = new User({
    mfa_phone_number: "555-111-****",
    email_address: "mock@gmail.com",
    mfa_delivery_preference: args.mfaEnabled ? "SMS" : "Opt Out",
  });
  const appLogic = useMockableAppLogic({
    portalFlow: {
      pathname: routes.user.settings,
    },
  });

  return <Settings appLogic={appLogic} user={user} />;
};
