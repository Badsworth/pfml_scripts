import { ConsentToDataSharing } from "src/pages/user/consent-to-data-sharing";
import { Props } from "types/common";
import React from "react";
import User from "src/models/User";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/User/Consent to data sharing",
  component: ConsentToDataSharing,
  argTypes: {
    query: {
      control: {
        type: "radio",
        options: ["Claimant Portal", "Employer Portal"],
      },
    },
  },
  args: {
    query: "Claimant Portal",
  },
};

export const Page = (
  args: Props<typeof ConsentToDataSharing> & { query: string }
) => {
  let user = new User({});

  if (args.query === "Employer Portal") {
    user = new User({ roles: [{ role_id: 2, role_description: "Employer" }] });
  }

  const appLogic = useMockableAppLogic();

  return <ConsentToDataSharing appLogic={appLogic} user={user} />;
};
