import { ImportClaim } from "src/pages/applications/import-claim";
import React from "react";
import User from "src/models/User";
import routes from "src/routes";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Applications/Import claim",
  component: ImportClaim,
  argTypes: {
    MFA: {
      control: {
        type: "radio",
        options: ["Opt Out", "SMS verified", "SMS unverified"],
      },
    },
  },
  args: {
    MFA: "Opt Out",
  },
};

export const Page = (args: {
  MFA: "Opt Out" | "SMS verified" | "SMS unverified";
}) => {
  const mfa_delivery_preferences = {
    "Opt Out": "Opt Out",
    "SMS verified": "SMS",
    "SMS unverified": "SMS",
  } as const;
  const mfa_delivery_preference = mfa_delivery_preferences[args.MFA];

  const user = new User({
    mfa_phone_number: {
      int_code: "1",
      phone_number: args.MFA === "Opt Out" ? null : "***-***-1234",
      phone_type: "Cell",
    },
    mfa_delivery_preference,
  });

  const appLogic = useMockableAppLogic({
    auth: {
      isPhoneVerified: () => Promise.resolve(args.MFA === "SMS verified"),
    },
    portalFlow: {
      pathname: routes.applications.importClaim,
    },
  });

  return <ImportClaim appLogic={appLogic} user={user} />;
};
