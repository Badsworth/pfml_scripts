import User, { UserLeaveAdministrator } from "src/models/User";
import { Index } from "src/pages/employers/organizations";
import React from "react";

export default {
  title: `Pages/Employers/Organizations/Organizations`,
  component: Index,
};

export const Default = () => {
  const user_leave_administrators = [
    new UserLeaveAdministrator({
      employer_dba: "Some Company",
      employer_fein: "11-11111",
      employer_id: "123",
      has_verification_data: true,
      verified: false,
    }),
  ];
  const user = new User({
    user_leave_administrators,
  });
  const appLogic = {
    portalFlow: {
      goTo: () => {},
    },
    users: {
      user,
    },
  };
  return <Index appLogic={appLogic} />;
};
