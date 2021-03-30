import { Dashboard } from "src/pages/employers/dashboard";
import React from "react";
import User from "src/models/User";
import routes from "src/routes";

export default {
  title: "Pages/Employers/Dashboard",
  component: Dashboard,
};

export const Default = () => {
  const appLogic = {
    portalFlow: {
      pathname: routes.employers.dashboard,
    },
  };
  const user = new User({
    user_leave_administrators: [
      {
        employer_dba: "Test Company",
        employer_fein: "",
        employer_id: 1,
        has_verification_data: true,
        verified: true,
      },
    ],
  });
  return <Dashboard appLogic={appLogic} user={user} />;
};
