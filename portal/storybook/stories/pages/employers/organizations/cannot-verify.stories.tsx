import { CannotVerify } from "src/pages/employers/organizations/cannot-verify";
import React from "react";
import User from "src/models/User";

export default {
  title: "Pages/Employers/Organizations/Cannot Verify",
  component: CannotVerify,
};

export const Default = () => {
  const query = { employer_id: "mock_employer_id" };
  const appLogic = {
    users: {
      user: new User({
        user_leave_administrators: [
          // @ts-expect-error ts-migrate(2741) FIXME: Property 'has_fineos_registration' is missing in t... Remove this comment to see the full error message
          {
            employer_dba: "Some Company",
            employer_fein: "11-11111",
            employer_id: "mock_employer_id",
            has_verification_data: true,
            verified: false,
          },
        ],
      }),
    },
  };
  return (
    <CannotVerify
      query={query}
      // @ts-expect-error ts-migrate(2322) FIXME: Type '{ query: { employer_id: string; }; appLogic:... Remove this comment to see the full error message
      appLogic={appLogic}
      user={appLogic.users.user}
    />
  );
};
