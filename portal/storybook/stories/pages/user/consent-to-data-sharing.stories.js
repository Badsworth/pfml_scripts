import { ConsentToDataSharing } from "src/pages/user/consent-to-data-sharing";
import React from "react";
import User from "src/models/User";

export default {
  title: "Pages/User/Consent to data sharing",
  component: ConsentToDataSharing,
};

export const Page = () => {
  const appLogic = {
    users: {},
  };

  return <ConsentToDataSharing appLogic={appLogic} user={new User()} />;
};
