import User, { RoleDescription, UserLeaveAdministrator } from "src/models/User";
import { ConvertToEmployee } from "src/pages/user/convert-to-employee";
import React from "react";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/User/Convert to Employee",
  component: ConvertToEmployee,
};

export const Page = () => {
  const user = new User({
    consented_to_data_sharing: true,
    roles: [
      {
        role_id: 1,
        role_description: RoleDescription.employer,
      },
    ],
    user_leave_administrators: [
      new UserLeaveAdministrator({
        employer_fein: "12-3456789",
        verified: false,
        has_fineos_registration: false,
        has_verification_data: false,
      }),
    ],
  });

  const appLogic = useMockableAppLogic();

  return <ConvertToEmployee appLogic={appLogic} user={user} />;
};
