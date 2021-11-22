import Claim, { AbsenceCaseStatusType, ClaimEmployee } from "src/models/Claim";
import React, { useState } from "react";
import User, { UserLeaveAdministrator } from "src/models/User";
import ClaimCollection from "src/models/ClaimCollection";
import { Dashboard } from "src/pages/employers/dashboard";
import { NullableQueryParams } from "src/utils/routeWithParams";
import { Props } from "storybook/types";
import dayjs from "dayjs";
import faker from "faker";
import routes from "src/routes";
import { times } from "lodash";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

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
  args: {
    claims: "Has claims",
    total_pages: 3,
    verification: Object.keys(verificationScenarios)[0],
  },
  argTypes: {
    claims: {
      control: {
        type: "radio",
        options: ["Has claims", "No claims"],
      },
    },
    total_pages: {
      control: {
        type: "number",
      },
    },
    verification: {
      control: {
        type: "radio",
        options: Object.keys(verificationScenarios),
      },
    },
  },
};

export const Default = (
  args: Props<typeof Dashboard> & {
    claims: string;
    total_pages: number;
    verification: keyof typeof verificationScenarios;
  }
) => {
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
              created_at: dayjs().subtract(num, "day").format("YYYY-MM-DD"),
              fineos_absence_id: `NTN-101-ABS-${num}`,
              claim_status: faker.helpers.randomize([
                "Approved",
                "Declined",
                "Closed",
                "Completed",
                "Adjudication",
                "Intake In Progress",
              ]) as AbsenceCaseStatusType,
              employee: new ClaimEmployee({
                first_name: faker.name.firstName(),
                last_name: faker.name.lastName(),
              }),
              employer: {
                employer_id: faker.datatype.uuid(),
                employer_dba: faker.company.companyName(),
                employer_fein: `${faker.finance.account(
                  2
                )}-${faker.finance.account(7)}`,
              },
              absence_period_end_date: "",
              absence_period_start_date: "",
              claim_type_description: "",
              fineos_notification_id: "",
              managed_requirements: [],
            })
        );

  const appLogic = useMockableAppLogic({
    claims: {
      claims: new ClaimCollection(claims),
      isLoadingClaims: false,
      paginationMeta: {
        page_offset: 1,
        page_size: 25,
        total_pages: hasNoClaims ? 1 : args.total_pages,
        total_records: hasNoClaims ? 0 : args.total_pages * 25,
        order_by: "created_at",
        order_direction: "ascending",
      },
    },
    portalFlow: {
      updateQuery: (params: NullableQueryParams) => {
        setQuery(params);
      },
      pathname: routes.employers.dashboard,
    },
    users: {
      user,
    },
  });

  return <Dashboard appLogic={appLogic} query={query} user={user} />;
};
