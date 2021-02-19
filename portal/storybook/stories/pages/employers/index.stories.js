import { Index } from "src/pages/employers";
import React from "react";
import User from "src/models/User";

export default {
  title: "Pages/Employers/Welcome",
  component: Index,
  argTypes: {
    hasVerifiableEmployer: {
      defaultValue: "Yes",
      control: {
        type: "radio",
        options: ["Yes", "No"],
      },
    },
  },
};

export const Default = ({ hasVerifiableEmployer }) => {
  const user = new User({
    user_leave_administrators: [
      {
        employer_dba: "Test Company",
        employer_fein: "",
        employer_id: 1,
        has_verification_data: true,
        verified: !(hasVerifiableEmployer === "Yes"),
      },
    ],
  });
  return <Index user={user} />;
};
