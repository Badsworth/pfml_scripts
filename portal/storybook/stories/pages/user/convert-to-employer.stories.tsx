import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import BenefitsApplicationCollection from "src/models/BenefitsApplicationCollection";
import { ConvertToEmployer } from "src/pages/user/convert-to-employer";
import React from "react";
import User from "src/models/User";

export default {
  title: "Pages/User/Convert to Employer",
  component: ConvertToEmployer,
};

export const Page = () => {
  // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
  const user = new User();

  const claims = new BenefitsApplicationCollection();

  const appLogic = {
    users: {
      convertUser: () => {},
    },
    appErrors: new AppErrorInfoCollection(),
  };

  // @ts-expect-error ts-migrate(2740) FIXME: Type '{ users: { convertUser: () => void; }; appEr... Remove this comment to see the full error message
  return <ConvertToEmployer appLogic={appLogic} user={user} claims={claims} />;
};
