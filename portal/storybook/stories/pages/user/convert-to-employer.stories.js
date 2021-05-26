import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import BenefitsApplicationCollection from "src/models/BenefitsApplicationCollection";
import { ConvertToEmployer } from "src/pages/user/convert-to-employer";
import React from "react";
import User from "src/models/User";

export default {
  title: "Pages/User/Convert to Employer",
  component: ConvertToEmployer,
};

export const Page = (args) => {
  const user = new User();

  const claims = new BenefitsApplicationCollection();

  const appLogic = {
    users: {
      convertUser: () => {},
    },
    appErrors: new AppErrorInfoCollection(),
  };

  return <ConvertToEmployer appLogic={appLogic} user={user} claims={claims} />;
};
