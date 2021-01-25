import { ConsentToDataSharing } from "src/pages/user/consent-to-data-sharing";
import React from "react";
import User from "src/models/User";

export default {
  title: "Pages/User/Consent to data sharing",
  component: ConsentToDataSharing,
};

export const Page = (args) => {
  let user = new User();
  if (args.query === "Employer Portal") {
    user = new User({ roles: [{ role_description: "Employer" }] });
  }

  const appLogic = {
    users: {
      updateUser: () => {},
    },
  };

  return <ConsentToDataSharing appLogic={appLogic} user={user} />;
};

Page.argTypes = {
  query: {
    defaultValue: "Default",
    control: {
      type: "radio",
      options: ["Claimant Portal", "Employer Portal"],
    },
  },
};
