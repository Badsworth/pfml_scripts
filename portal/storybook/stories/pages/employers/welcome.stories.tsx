import User, { UserLeaveAdministrator } from "src/models/User";
import React from "react";
import { Welcome } from "src/pages/employers/welcome";
import routes from "src/routes";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Employers/Welcome",
  component: Welcome,
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

export const Default = ({
  hasVerifiableEmployer,
}: {
  hasVerifiableEmployer: string;
}) => {
  const user = new User({
    user_leave_administrators: [
      new UserLeaveAdministrator({
        employer_dba: "Test Company",
        employer_fein: "",
        employer_id: "1",
        has_verification_data: true,
        verified: !(hasVerifiableEmployer === "Yes"),
      }),
    ],
  });
  const appLogic = useMockableAppLogic({
    portalFlow: {
      pathname: routes.employers.welcome,
    },
  });

  return <Welcome appLogic={appLogic} user={user} />;
};
