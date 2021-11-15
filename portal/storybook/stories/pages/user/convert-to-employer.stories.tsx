import BenefitsApplicationCollection from "src/models/BenefitsApplicationCollection";
import { ConvertToEmployer } from "src/pages/user/convert-to-employer";
import React from "react";
import User from "src/models/User";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/User/Convert to Employer",
  component: ConvertToEmployer,
};

export const Page = () => {
  const user = new User({});
  const claims = new BenefitsApplicationCollection();
  const appLogic = useMockableAppLogic();

  return <ConvertToEmployer appLogic={appLogic} user={user} claims={claims} />;
};
