import User, { UserLeaveAdministrator } from "src/models/User";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import React from "react";
import VerifyContributions from "src/pages/employers/organizations/verify-contributions";
import Withholding from "src/models/Withholding";

export default {
  title: "Pages/Employers/Organizations/Verify Contributions",
  component: VerifyContributions,
};

export const Default = () => {
  const query = {
    employer_id: "mock_employer_id",
    next: "/employers/organizations",
  };
  const user = new User({
    user_leave_administrators: [
      new UserLeaveAdministrator({
        employer_dba: "Some Company",
        employer_fein: "11-11111",
        employer_id: "123",
        verified: false,
      }),
    ],
  });
  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    employers: {
      submitWithholding: () => {},
    },
    auth: {
      isLoggedIn: true,
      requireLogin: () => {},
    },
    portalFlow: {
      pathname: "/employers/organizations/verify-contributions",
    },
    users: {
      loadUser: () => {},
      requireUserConsentToDataAgreement: () => {},
      requireUserRole: () => {},
      user,
    },
  };
  const withholding = new Withholding({
    filing_period: "1-1-2021",
  });
  return (
    <VerifyContributions
      appLogic={appLogic}
      query={query}
      user={user}
      withholding={withholding}
    />
  );
};
