import User, { UserLeaveAdministrator } from "src/models/User";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import React from "react";
import VerifyBusiness from "src/pages/employers/verify-business";

export default {
  title: "Pages/Employers/Auth/Verify Business",
  component: VerifyBusiness,
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
      pathname: "/employers/verify-business",
    },
    users: {
      loadUser: () => {},
      requireUserConsentToDataAgreement: () => {},
      requireUserRole: () => {},
      user,
    },
  };
  return <VerifyBusiness appLogic={appLogic} query={query} user={user} />;
};
