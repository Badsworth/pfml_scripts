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
    smsMfaConfirmed: {
      control: {
        type: "boolean",
      },
    },
  },
  args: {
    mfaEnabled: false,
    smsMfaConfirmed: false,
  },
};

export const Page = (args: {
  mfaEnabled: boolean;
  smsMfaConfirmed: boolean;
}) => {
  const user = new User({
    mfa_phone_number: {
      int_code: "1",
      phone_number: "***-***-1234",
      phone_type: "Cell",
    },
    email_address: "mock@gmail.com",
    mfa_delivery_preference: args.mfaEnabled ? "SMS" : "Opt Out",
  });
  const appLogic = useMockableAppLogic({
    portalFlow: {
      pathname: routes.user.settings,
    },
  });

  const query = args.smsMfaConfirmed ? { smsMfaConfirmed: "true" } : {};

  return <Settings appLogic={appLogic} user={user} query={query} />;
};
