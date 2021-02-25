import User, { UserLeaveAdministrator } from "src/models/User";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import React from "react";
import { VerifyContributions } from "src/pages/employers/organizations/verify-contributions";
import Withholding from "src/models/Withholding";

export default {
  title: "Pages/Employers/Organizations/Verify Contributions",
  component: VerifyContributions,
};

export const Default = () => {
  const query = {
    employer_id: "mock_employer_id",
  };
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
  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    employers: {
      loadClaim: () => {},
      submitWithholding: () => {},
    },
    portalFlow: {
      goTo: () => {},
    },
    users: {
      user,
    },
    setAppErrors: () => {},
  };
  const withholding = new Withholding({
    filing_period: "02-2020",
  });
  return (
    <VerifyContributions
      query={query}
      appLogic={appLogic}
      withholding={withholding}
    />
  );
};
