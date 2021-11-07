import User, { UserLeaveAdministrator } from "src/models/User";
import React from "react";
import { Success } from "src/pages/employers/organizations/success";

export default {
  title: `Pages/Employers/Organizations/Verification Success`,
  component: Success,
};

export const Default = () => {
  const query = {
    employer_id: "123",
    next: "/",
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
  // @ts-expect-error ts-migrate(2740) FIXME: Type '{ portalFlow: { goTo: () => void; }; }' is m... Remove this comment to see the full error message
  return <Success appLogic={appLogic} query={query} user={user} />;
};
