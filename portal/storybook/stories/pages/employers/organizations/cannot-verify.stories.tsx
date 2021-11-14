import User, { UserLeaveAdministrator } from "src/models/User";
import { CannotVerify } from "src/pages/employers/organizations/cannot-verify";
import React from "react";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Employers/Organizations/Cannot Verify",
  component: CannotVerify,
};

export const Default = () => {
  const query = { employer_id: "mock_employer_id" };
  const user = new User({
    user_leave_administrators: [
      new UserLeaveAdministrator({
        employer_dba: "Some Company",
        employer_fein: "11-11111",
        employer_id: "mock_employer_id",
        has_verification_data: true,
        verified: false,
      }),
    ],
  });

  const appLogic = useMockableAppLogic();

  return <CannotVerify query={query} appLogic={appLogic} user={user} />;
};
