import React, { useState } from "react";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import Claim from "src/models/Claim";
import { Dashboard } from "src/pages/employers/dashboard";
import { NullableQueryParams } from "src/utils/routeWithParams";
import { Props } from "types/common";
import User from "src/models/User";
import createAbsencePeriod from "lib/mock-helpers/createAbsencePeriod";
import createMockClaim from "lib/mock-helpers/createMockClaim";
import { createMockManagedRequirement } from "lib/mock-helpers/createMockManagedRequirement";
import createMockUserLeaveAdministrator from "lib/mock-helpers/createMockUserLeaveAdministrator";
import { faker } from "@faker-js/faker";
import routes from "src/routes";
import { times } from "lodash";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

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
        createMockUserLeaveAdministrator({
          has_fineos_registration: true,
          has_verification_data: true,
          verified: true,
        }),
        createMockUserLeaveAdministrator({
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
        createMockUserLeaveAdministrator({
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
        createMockUserLeaveAdministrator({
          has_verification_data: false,
          verified: false,
        }),
      ],
    }),
  },
  "All employers not verified + verifiable": {
    user: createUser({
      user_leave_administrators: [
        createMockUserLeaveAdministrator({
          has_verification_data: true,
          verified: false,
        }),
      ],
    }),
  },
  "Mix of verified and verifiable employers": {
    user: createUser({
      user_leave_administrators: [
        createMockUserLeaveAdministrator({
          has_fineos_registration: true,
          has_verification_data: true,
          verified: true,
        }),
        createMockUserLeaveAdministrator({
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
        createMockUserLeaveAdministrator({
          has_fineos_registration: true,
          has_verification_data: true,
          verified: true,
        }),
        createMockUserLeaveAdministrator({
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
      : times(25, () => {
          const absence_periods = times(
            faker.datatype.number({ min: 1, max: 3 }),
            () => createAbsencePeriod()
          );

          const claim = createMockClaim({
            absence_periods,
            managed_requirements: [
              createMockManagedRequirement({
                follow_up_date: faker.date.future().toISOString(),
                // Create an open managed requirement if any absence period is in a pending-like state
                status: absence_periods.some(
                  (period) =>
                    period.request_decision === "In Review" ||
                    period.request_decision === "Pending"
                )
                  ? "Open"
                  : "Complete",
              }),
            ],
          });

          return claim;
        });

  const appLogic = useMockableAppLogic({
    claims: {
      claims: new ApiResourceCollection<Claim>("fineos_absence_id", claims),
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
