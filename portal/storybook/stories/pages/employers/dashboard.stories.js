import Claim, { ClaimEmployee, ClaimEmployer } from "src/models/Claim";
import React, { useState } from "react";
import User, { UserLeaveAdministrator } from "src/models/User";
import AppErrorInfoCollection from "src/models/AppErrorInfoCollection";
import ClaimCollection from "src/models/ClaimCollection";
import { Dashboard } from "src/pages/employers/dashboard";
import { DateTime } from "luxon";
import PaginationMeta from "src/models/PaginationMeta";
import faker from "faker";
import routes from "src/routes";
import { times } from "lodash";

function createUserLeaveAdministrator(attrs = {}) {
  return new UserLeaveAdministrator({
    employer_id: faker.datatype.uuid(),
    employer_dba: faker.company.companyName(),
    employer_fein: `${faker.finance.account(2)}-${faker.finance.account(7)}`,
    ...attrs,
  });
}

function createUser(attrs = {}) {
  return new User({
    consented_to_data_sharing: true,
    ...attrs,
  });
}

const verificationScenarios = {
  "All employers verified": {
    user: createUser({
      user_leave_administrators: [
        createUserLeaveAdministrator({
          has_fineos_registration: true,
          has_verification_data: true,
          verified: true,
        }),
        createUserLeaveAdministrator({
          has_fineos_registration: true,
          has_verification_data: true,
          verified: true,
        }),
      ],
    }),
  },
  "Single verified employer, not registered in FINEOS": {
    user: createUser({
      user_leave_administrators: [
        createUserLeaveAdministrator({
          has_fineos_registration: false,
          has_verification_data: true,
          verified: true,
        }),
      ],
    }),
  },
  "All employers not verified + unverifiable": {
    user: createUser({
      user_leave_administrators: [
        createUserLeaveAdministrator({
          has_verification_data: false,
          verified: false,
        }),
      ],
    }),
  },
  "All employers not verified + verifiable": {
    user: createUser({
      user_leave_administrators: [
        createUserLeaveAdministrator({
          has_verification_data: true,
          verified: false,
        }),
      ],
    }),
  },
  "Mix of verified and verifiable employers": {
    user: createUser({
      user_leave_administrators: [
        createUserLeaveAdministrator({
          has_fineos_registration: true,
          has_verification_data: true,
          verified: true,
        }),
        createUserLeaveAdministrator({
          has_fineos_registration: true,
          has_verification_data: true,
          verified: false,
        }),
      ],
    }),
  },
  "Mix of verified and unverifiable employers": {
    user: createUser({
      user_leave_administrators: [
        createUserLeaveAdministrator({
          has_fineos_registration: true,
          has_verification_data: true,
          verified: true,
        }),
        createUserLeaveAdministrator({
          has_fineos_registration: true,
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
    total_pages: {
      defaultValue: 3,
      control: {
        type: "number",
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
  const hasNoClaims = args.claims === "No claims";
  const [query, setQuery] = useState({});

  const claims =
    args.claims === "No claims"
      ? []
      : times(
          25,
          (num) =>
            new Claim({
              created_at: DateTime.local().minus({ days: num }).toISODate(),
              fineos_absence_id: `NTN-101-ABS-${num}`,
              claim_status: faker.helpers.randomize([
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
              employer: new ClaimEmployer(
                faker.helpers.randomize(
                  user.user_leave_administrators.filter((la) => la.verified)
                )
              ),
            })
        );

  const mockFunction = () => {};
  const appLogic = {
    appErrors: new AppErrorInfoCollection(),
    auth: {
      isLoggedIn: true,
      requireLogin: mockFunction,
    },
    claims: {
      claims: new ClaimCollection(claims),
      isLoadingClaims: false,
      loadPage: mockFunction,
      paginationMeta: new PaginationMeta({
        page_offset: 1,
        page_size: 25,
        total_pages: hasNoClaims ? 1 : args.total_pages,
        total_records: hasNoClaims ? 0 : args.total_pages * 25,
        order_by: "created_at",
        order_direction: "asc",
      }),
    },
    portalFlow: {
      getNextPageRoute: () => "#mock-route",
      updateQuery: (params) => {
        setQuery(params);
      },
      pathname: routes.employers.dashboard,
    },
    users: {
      loadUser: mockFunction,
      requireUserConsentToDataAgreement: mockFunction,
      requireUserRole: mockFunction,
      user,
    },
  };

  return <Dashboard appLogic={appLogic} query={query} user={user} />;
};
