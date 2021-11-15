import User, { UserLeaveAdministrator } from "src/models/User";
import React from "react";
import { VerifyContributions } from "src/pages/employers/organizations/verify-contributions";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Employers/Organizations/Verify Contributions",
  component: VerifyContributions,
};

export const Default = () => {
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
  const withholding = {
    filing_period: "02-2020",
  };

  return (
    <VerifyContributions
      query={{}}
      appLogic={appLogic}
      withholding={withholding}
      employer={user.user_leave_administrators[0]}
      user={user}
    />
  );
};
