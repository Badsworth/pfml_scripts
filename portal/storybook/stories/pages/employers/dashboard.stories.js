import Claim, { ClaimEmployee, ClaimEmployer } from "src/models/Claim";
import User, { UserLeaveAdministrator } from "src/models/User";
import ClaimCollection from "src/models/ClaimCollection";
import { Dashboard } from "src/pages/employers/dashboard";
import { DateTime } from "luxon";
import React from "react";
import faker from "faker";
import routes from "src/routes";
import { times } from "lodash";

function createUserLeaveAdministrator(attrs = {}) {
  return new UserLeaveAdministrator(attrs);
}

const verificationScenarios = {
  "All employers verified": {
    user: new User({
      user_leave_administrators: [
        createUserLeaveAdministrator({
          has_verification_data: true,
          verified: true,
        }),
        createUserLeaveAdministrator({
          has_verification_data: true,
          verified: true,
        }),
      ],
    }),
  },
  "Single verified employer": {
    user: new User({
      user_leave_administrators: [
        createUserLeaveAdministrator({
          has_verification_data: true,
          verified: true,
        }),
      ],
    }),
  },
  "All employers not verified + unverifiable": {
    user: new User({
      user_leave_administrators: [
        createUserLeaveAdministrator({
          has_verification_data: false,
          verified: false,
        }),
      ],
    }),
  },
  "All employers not verified + verifiable": {
    user: new User({
      user_leave_administrators: [
        createUserLeaveAdministrator({
          has_verification_data: true,
          verified: false,
        }),
      ],
    }),
  },
  "Mix of verified and verifiable employers": {
    user: new User({
      user_leave_administrators: [
        createUserLeaveAdministrator({
          has_verification_data: true,
          verified: true,
        }),
        createUserLeaveAdministrator({
          has_verification_data: true,
          verified: false,
        }),
      ],
    }),
  },
  "Mix of verified and unverifiable employers": {
    user: new User({
      user_leave_administrators: [
        createUserLeaveAdministrator({
          has_verification_data: true,
          verified: true,
        }),
        createUserLeaveAdministrator({
          has_verification_data: false,
          verified: false,
        }),
      ],
    }),
  },
};

export default {
  title: "Pages/Employers/Dashboard",
  component: Dashboard,
  argTypes: {
    claims: {
      defaultValue: "Has claims",
      control: {
        type: "radio",
        options: ["Has claims", "No claims"],
      },
    },
    verification: {
      defaultValue: Object.keys(verificationScenarios)[0],
      control: {
        type: "radio",
        options: Object.keys(verificationScenarios),
      },
    },
  },
};

export const Default = (args) => {
  const { user } = verificationScenarios[args.verification];
  const hasMultipleEmployers = user.user_leave_administrators.length > 1;
  const claims =
    args.claims === "No claims"
      ? []
      : times(
          25,
          (num) =>
            new Claim({
              created_at: DateTime.local().minus({ days: num }).toISODate(),
              fineos_absence_id: `NTN-101-ABS-${num}`,
              fineos_absence_status: faker.helpers.randomize([
                "Approved",
                "Declined",
                "Closed",
                "Completed",
                "Adjudication",
                "Intake In Progress",
              ]),
              employee: new ClaimEmployee({
                first_name: faker.name.firstName(),
                last_name: faker.name.lastName(),
              }),
              employer: new ClaimEmployer({
                employer_dba: hasMultipleEmployers
                  ? faker.company.companyName()
                  : "Dunder-Mifflin",
                employer_fein: hasMultipleEmployers
                  ? faker.finance.routingNumber().replace(/(\d\d)/, "$1-")
                  : "82-9471234",
              }),
            })
        );

  const appLogic = {
    portalFlow: {
      getNextPageRoute: () => {},
      goTo: () => {},
      pathname: routes.employers.dashboard,
    },
  };

  return (
    <Dashboard
      appLogic={appLogic}
      claims={new ClaimCollection(claims)}
      user={user}
    />
  );
};
