import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import { Index } from "src/pages/employers";
import React from "react";
import User from "src/models/User";

export default {
  title: "Pages/Employers/Applications/Welcome",
  component: Index,
  argTypes: {
    hasUnverifiedEmployer: {
      defaultValue: "Yes",
      control: {
        type: "radio",
        options: ["Yes", "No"],
      },
    },
  },
};

export const Default = ({ hasUnverifiedEmployer }) => {
  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    users: {
      user: new User({
        user_leave_administrators: [
          {
            employer_dba: "Test Company",
            employer_fein: "",
            employer_id: 1,
            verified: !(hasUnverifiedEmployer === "Yes"),
          },
        ],
      }),
    },
  };
  return <Index appLogic={appLogic} />;
};
