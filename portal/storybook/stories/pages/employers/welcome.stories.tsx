import React from "react";
import User from "src/models/User";
import { Welcome } from "src/pages/employers/welcome";
import routes from "src/routes";

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
  const appLogic = {
    portalFlow: {
      pathname: routes.employers.welcome,
    },
  };
  const user = new User({
    user_leave_administrators: [
      {
        employer_dba: "Test Company",
        employer_fein: "",
        // @ts-expect-error ts-migrate(2322) FIXME: Type 'number' is not assignable to type 'string'.
        employer_id: 1,
        has_verification_data: true,
        verified: !(hasVerifiableEmployer === "Yes"),
      },
    ],
  });
  // @ts-expect-error ts-migrate(2740) FIXME: Type '{ portalFlow: { pathname: string; }; }' is m... Remove this comment to see the full error message
  return <Welcome appLogic={appLogic} user={user} />;
};
