import User, { UserLeaveAdministrator } from "src/models/User";
import React from "react";
import { VerificationSuccess } from "src/pages/employers/verification-success";

export default {
  title: `Pages/Employers/VerificationSuccess`,
  component: VerificationSuccess,
};

export const Default = () => {
  const query = {
    employer_id: "123",
  };
  const appLogic = {
    portalFlow: {
      goTo: () => {},
    },
  };
  const user_leave_administrators = [
    new UserLeaveAdministrator({
      employer_dba: "Some Company",
      employer_fein: "11-11111",
      employer_id: "123",
      verified: false,
    }),
  ];
  const user = new User({
    user_leave_administrators,
  });
  return <VerificationSuccess appLogic={appLogic} query={query} user={user} />;
};
