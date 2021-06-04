import User, { UserLeaveAdministrator } from "src/models/User";
import { Index } from "src/pages/employers/organizations";
import React from "react";

const ORGANIZATION_TYPES = {
  verified: "Verified employer",
  verificationRequired: "Not verified employer (verification required)",
  verificationBlocked: "Not verified employer (verification blocked)",
};

export default {
  title: `Pages/Employers/Organizations/Organizations`,
  component: Index,
  argTypes: {
    organizations: {
      control: {
        type: "check",
        options: Object.values(ORGANIZATION_TYPES),
      },
    },
  },
};

export const Default = (args) => {
  const organizations = args.organizations || [];
  const user_leave_administrators = [];

  if (organizations.includes(ORGANIZATION_TYPES.verified)) {
    user_leave_administrators.push(
      new UserLeaveAdministrator({
        employer_dba: "Knitting Castle",
        employer_fein: "11-0003443",
        employer_id: "dda930f-93jfk-iej08",
        has_verification_data: true,
        verified: true,
      })
    );
  }

  if (organizations.includes(ORGANIZATION_TYPES.verificationRequired)) {
    user_leave_administrators.push(
      new UserLeaveAdministrator({
        employer_dba: "Book Bindings 'R Us",
        employer_fein: "22-0001823",
        employer_id: "dda903f-f093f-ff900",
        has_verification_data: true,
        verified: false,
      })
    );
  }

  if (organizations.includes(ORGANIZATION_TYPES.verificationBlocked)) {
    user_leave_administrators.push(
      new UserLeaveAdministrator({
        employer_dba: "Tomato Touchdown",
        employer_fein: "33-0007192",
        employer_id: "io19fj9-00jjf-uiw3r",
        has_verification_data: false,
        verified: false,
      })
    );
  }

  const user = new User({
    user_leave_administrators,
  });
  const appLogic = {
    users: {
      user,
    },
    portalFlow: {
      getNextPageRoute: () => "",
    },
  };
  return <Index appLogic={appLogic} />;
};
