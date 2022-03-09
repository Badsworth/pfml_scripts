import Claim, { ClaimEmployee } from "../../../src/models/Claim";
import { cleanup, screen, within } from "@testing-library/react";
import { createAbsencePeriod, renderPage } from "../../test-utils";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import { AppLogic } from "../../../src/hooks/useAppLogic";
import Dashboard from "../../../src/pages/employers/dashboard";
import MockDate from "mockdate";
import PaginationMeta from "../../../src/models/PaginationMeta";
import User from "../../../src/models/User";
import createMockClaim from "../../../lib/mock-helpers/createMockClaim";
import { createMockManagedRequirement } from "../../../lib/mock-helpers/createMockManagedRequirement";
import createMockUserLeaveAdministrator from "../../../lib/mock-helpers/createMockUserLeaveAdministrator";
import routes from "../../../src/routes";
import userEvent from "@testing-library/user-event";

// Avoid issue where USWDS generates unique ID each render,
// which causes havoc for our snapshot testing
// https://github.com/uswds/uswds/issues/4338
// TODO (PORTAL-1560): Remove this mock, once the new deprecated table component is removed
jest.mock("../../../src/components/core/TooltipIcon", () => ({
  __esModule: true,
  default: () => null,
}));

const MOCK_CURRENT_ISO_DATE = "2021-05-01";

const verifiedUserLeaveAdministrator = createMockUserLeaveAdministrator({
  employer_dba: "Work Inc",
  employer_fein: "12-3456789",
  has_fineos_registration: true,
  has_verification_data: true,
  verified: true,
});

const verifiableUserLeaveAdministrator = createMockUserLeaveAdministrator({
  employer_dba: "Book Bindings 'R Us",
  has_fineos_registration: false,
  has_verification_data: true,
  verified: false,
});

const getClaim = (customAttrs: Partial<Claim> = {}) => {
  // Stable data to support stable snapshots
  return createMockClaim({
    absence_periods: [
      createAbsencePeriod({
        absence_period_start_date: "2020-01-01",
        absence_period_end_date: "2020-02-01",
        reason: "Serious Health Condition - Employee",
        request_decision: "Approved",
        period_type: "Continuous",
      }),
    ],
    created_at: "2021-01-15",
    managed_requirements: [],
    employee: new ClaimEmployee({
      first_name: "Jane",
      middle_name: null,
      last_name: "Doe",
    }),
    employer: {
      employer_dba: verifiedUserLeaveAdministrator.employer_dba,
      employer_fein: verifiedUserLeaveAdministrator.employer_fein,
      employer_id: verifiedUserLeaveAdministrator.employer_id,
    },
    fineos_absence_id: "NTN-111-ABS-01",
    claim_status: "Approved",
    ...customAttrs,
  });
};

const setup = (options?: {
  claims?: Claim[];
  userAttrs?: Partial<User>;
  paginationMeta?: Partial<PaginationMeta>;
  query?: { [key: string]: string };
}) => {
  let updateQuerySpy;
  const {
    claims = [],
    userAttrs = {},
    paginationMeta = {},
    query = {},
  } = options ?? {};

  const locationCopy = { ...window.location };
  // @ts-expect-error Need to manually set window.location so that we can set the active query string
  delete window.location;
  window.location = {
    ...locationCopy,
    search: `?${new URLSearchParams(query)}`,
  };

  const setupAppLogic = (appLogic: AppLogic) => {
    // Fulfill the needs of withClaims to simulate that the user can view the page,
    // and that a list of claims has been loaded
    appLogic.users.user = new User({
      consented_to_data_sharing: true,
      ...userAttrs,
    });
    appLogic.claims.claims = new ApiResourceCollection<Claim>(
      "fineos_absence_id",
      claims
    );
    appLogic.claims.isLoadingClaims = false;
    appLogic.claims.paginationMeta = {
      page_offset: 1,
      page_size: 25,
      total_pages: 3,
      total_records: 75,
      order_by: "created_at",
      order_direction: "ascending",
      ...paginationMeta,
    };

    updateQuerySpy = jest.spyOn(appLogic.portalFlow, "updateQuery");
  };

  const utils = renderPage(
    Dashboard,
    {
      addCustomSetup: setupAppLogic,
      pathname: routes.employers.dashboard,
    },
    {
      query,
    }
  );

  return {
    updateQuerySpy,
    ...utils,
  };
};

describe("Employer dashboard", () => {
  beforeAll(() => {
    MockDate.set(MOCK_CURRENT_ISO_DATE);
  });

  it("renders the page with expected content and pagination components", () => {
    const { container } = setup();

    expect(container).toMatchSnapshot();
  });

  // TODO (PORTAL-1560): Remove this test, once the deprecated table component is removed
  it("deprecated: renders a table of claims with links if employer is registered in FINEOS", () => {
    const claims = [getClaim()];
    const userAttrs = {
      // Set multiple employers so the table shows all possible columns
      user_leave_administrators: [
        verifiedUserLeaveAdministrator,
        verifiableUserLeaveAdministrator,
      ],
    };

    setup({ claims, userAttrs });

    expect(screen.getByRole("table")).toMatchSnapshot();
  });

  it("renders a table of claims, with links to status page", () => {
    process.env.featureFlags = JSON.stringify({
      employerShowMultiLeaveDashboard: true,
    });
    const claims = [
      getClaim({
        managed_requirements: [
          createMockManagedRequirement({
            follow_up_date: MOCK_CURRENT_ISO_DATE,
            // "Open" helps provide coverage of the link used on the Review button
            status: "Open",
          }),
        ],
      }),
    ];

    const userAttrs = {
      user_leave_administrators: [
        // Set multiple employers so the table shows all possible columns
        verifiedUserLeaveAdministrator,
        verifiableUserLeaveAdministrator,
      ],
    };

    setup({ claims, userAttrs });

    expect(screen.getByRole("table")).toMatchSnapshot();
  });

  // TODO (PORTAL-1560): Remove this test, once the deprecated table component is removed
  it("deprecated: renders claim rows without links if employer is not registered in FINEOS", () => {
    const verifiedButNotInFineos = {
      ...verifiableUserLeaveAdministrator,
      verified: true,
    };
    const claims = [
      getClaim({
        employer: {
          employer_dba: verifiedButNotInFineos.employer_dba,
          employer_fein: verifiedButNotInFineos.employer_fein,
          employer_id: verifiedButNotInFineos.employer_id,
        },
      }),
    ];

    const userAttrs = {
      user_leave_administrators: [verifiedButNotInFineos],
    };

    setup({ claims, userAttrs });
    expect(
      within(screen.getByRole("table")).queryByRole("link")
    ).not.toBeInTheDocument();
  });

  // TODO (PORTAL-1560) Remove the .each portion once flag is always enabled
  it.each([true, false])(
    "renders '--' when a Claim's Employee name is blank",
    (employerShowMultiLeaveDashboard) => {
      process.env.featureFlags = JSON.stringify({
        employerShowMultiLeaveDashboard,
      });
      let claims = [getClaim()];
      claims = claims.map((claim) => {
        claim.employee = null;
        return claim;
      });

      setup({
        claims,
        userAttrs: {
          user_leave_administrators: [verifiedUserLeaveAdministrator],
        },
      });

      expect(screen.getByRole("rowheader", { name: /--/ })).toBeInTheDocument();
    }
  );

  // TODO (PORTAL-1560): Remove this test, once the deprecated table component is removed
  it("deprecated: renders Organization column only when user has more than one Employer", () => {
    // Organization column should NOT
    setup({
      userAttrs: {
        user_leave_administrators: [verifiedUserLeaveAdministrator],
      },
    });

    expect(screen.getAllByRole("columnheader").map((el) => el.textContent))
      .toMatchInlineSnapshot(`
      [
        "Employee name",
        "Application ID",
        "Employer ID number",
        "Application start date",
        "Status",
      ]
    `);

    cleanup();

    // Organization column should show
    setup({
      userAttrs: {
        user_leave_administrators: [
          verifiedUserLeaveAdministrator,
          verifiableUserLeaveAdministrator,
        ],
      },
    });

    expect(screen.getAllByRole("columnheader").map((el) => el.textContent))
      .toMatchInlineSnapshot(`
      [
        "Employee name",
        "Application ID",
        "Organization",
        "Employer ID number",
        "Application start date",
        "Status",
      ]
    `);
  });

  it("renders Organization column only when user has more than one Employer", () => {
    process.env.featureFlags = JSON.stringify({
      employerShowMultiLeaveDashboard: true,
    });

    // Organization column should NOT show
    setup({
      userAttrs: {
        user_leave_administrators: [verifiedUserLeaveAdministrator],
      },
    });

    expect(screen.getAllByRole("columnheader").map((el) => el.textContent))
      .toMatchInlineSnapshot(`
      [
        "Employee (Application ID)",
        "Leave details",
        "Review due date",
      ]
    `);

    cleanup();

    // Organization column should show
    setup({
      userAttrs: {
        user_leave_administrators: [
          verifiedUserLeaveAdministrator,
          verifiableUserLeaveAdministrator,
        ],
      },
    });

    expect(screen.getAllByRole("columnheader").map((el) => el.textContent))
      .toMatchInlineSnapshot(`
      [
        "Employee (Application ID)",
        "Organization (FEIN)",
        "Leave details",
        "Review due date",
      ]
    `);
  });

  // TODO (PORTAL-1560) Remove the .each portion once flag is always enabled
  it.each([true, false])(
    "renders a 'no results' message in the table, and no pagination components when no claims are present",
    (employerShowMultiLeaveDashboard) => {
      process.env.featureFlags = JSON.stringify({
        employerShowMultiLeaveDashboard,
      });

      setup({
        userAttrs: {
          user_leave_administrators: [verifiedUserLeaveAdministrator],
        },
        paginationMeta: {
          total_records: 0,
          total_pages: 1,
        },
      });

      expect(
        screen.getByRole("cell", { name: "No applications on file" })
      ).toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /next/i })
      ).not.toBeInTheDocument();
    }
  );

  // TODO (PORTAL-1560) Remove the .each portion once flag is always enabled
  // eslint-disable-next-line jest/no-focused-tests
  it.each([true, false])(
    "renders a verification message in the table, when all employers are unverified",
    (employerShowMultiLeaveDashboard) => {
      process.env.featureFlags = JSON.stringify({
        employerShowMultiLeaveDashboard,
      });

      setup({
        userAttrs: {
          user_leave_administrators: [verifiableUserLeaveAdministrator],
        },
      });

      expect(
        screen.getByRole("cell", {
          name: /You have not verified any organizations/,
        })
      ).toMatchSnapshot();
    }
  );

  // TODO (PORTAL-1560) Remove the .each portion once flag is always enabled
  it.each([true, false])(
    "renders only the pagination summary when only one page of claims exists",
    (employerShowMultiLeaveDashboard) => {
      process.env.featureFlags = JSON.stringify({
        employerShowMultiLeaveDashboard,
      });
      setup({
        paginationMeta: {
          total_records: 25,
          total_pages: 1,
        },
      });

      expect(screen.getByText(/Viewing 1 to 25 of 25/i)).toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /next/i })
      ).not.toBeInTheDocument();
    }
  );

  // TODO (PORTAL-1560) Remove the .each portion once flag is always enabled
  it.each([true, false])(
    "changes the page_offset query param when a page navigation button is clicked",
    (employerShowMultiLeaveDashboard) => {
      process.env.featureFlags = JSON.stringify({
        employerShowMultiLeaveDashboard,
      });
      const { updateQuerySpy } = setup({
        paginationMeta: {
          page_offset: 2,
          total_pages: 3,
        },
      });

      userEvent.click(screen.getByRole("button", { name: /next/i }));

      expect(updateQuerySpy).toHaveBeenCalledWith({
        page_offset: "3",
      });
    }
  );

  it("renders the banner if there are any unverified employers", () => {
    setup({
      userAttrs: {
        user_leave_administrators: [
          // Mix of verified and unverified
          verifiedUserLeaveAdministrator,
          verifiableUserLeaveAdministrator,
        ],
      },
    });

    expect(screen.getAllByRole("region")[0]).toMatchSnapshot();
  });

  it("updates search param when a search is performed", () => {
    const { updateQuerySpy } = setup();

    userEvent.type(
      screen.getByRole("textbox", { name: /search/i }),
      "Bud Baxter"
    );
    userEvent.click(screen.getByRole("button", { name: /search/i }));

    expect(updateQuerySpy).toHaveBeenCalledWith({
      page_offset: "1",
      search: "Bud Baxter",
    });
  });

  it("clears search param when the search field is cleared", () => {
    const { updateQuerySpy } = setup({ query: { search: "Bud Baxter" } });

    userEvent.clear(screen.getByRole("textbox", { name: /search/i }));
    userEvent.click(screen.getByRole("button", { name: /search/i }));

    expect(updateQuerySpy).toHaveBeenCalledWith({
      page_offset: "1",
    });
  });

  it("sets initial filter form state from query prop", () => {
    process.env.featureFlags = JSON.stringify({
      employerShowMultiLeaveDashboard: true,
    });
    // Include multiple LA's so Employer filter shows
    const user_leave_administrators = [
      createMockUserLeaveAdministrator({
        verified: true,
      }),
      createMockUserLeaveAdministrator({
        verified: true,
      }),
    ];

    setup({
      query: {
        request_decision: "approved",
        employer_id: user_leave_administrators[0].employer_id,
      },
      userAttrs: {
        user_leave_administrators,
      },
    });

    userEvent.click(screen.getByRole("button", { name: /Show filters/i }));

    expect(
      screen.getByRole("combobox", { name: /organizations/i })
    ).toHaveValue(
      `${user_leave_administrators[0].employer_dba} (${user_leave_administrators[0].employer_fein})`
    );
    expect(screen.getByRole("radio", { name: /approved/i })).toBeChecked();
    expect(screen.getByRole("radio", { name: /denied/i })).not.toBeChecked();
  });

  it("updates query params when user changes filter to Approved", () => {
    process.env.featureFlags = JSON.stringify({
      employerShowMultiLeaveDashboard: true,
    });
    const { updateQuerySpy } = setup({
      paginationMeta: {
        page_offset: 2,
      },
    });

    userEvent.click(screen.getByRole("button", { name: /show filters/i }));
    userEvent.click(screen.getByRole("radio", { name: "Approved" }));
    userEvent.click(screen.getByRole("button", { name: /apply/i }));

    expect(updateQuerySpy).toHaveBeenCalledWith({
      request_decision: "approved",
      page_offset: "1",
    });
  });

  it("resets query params when user clicks Reset action", () => {
    process.env.featureFlags = JSON.stringify({
      employerShowMultiLeaveDashboard: true,
    });
    const user_leave_administrators = [
      createMockUserLeaveAdministrator({
        verified: true,
      }),
      createMockUserLeaveAdministrator({
        verified: true,
      }),
    ];

    const { updateQuerySpy } = setup({
      query: {
        request_decision: "approved",
        employer_id: user_leave_administrators[0].employer_id,
      },
      userAttrs: {
        user_leave_administrators,
      },
      paginationMeta: {
        page_offset: 2,
      },
    });

    userEvent.click(screen.getByRole("button", { name: /show filters/i }));
    userEvent.click(screen.getByRole("button", { name: /reset/i }));

    expect(updateQuerySpy).toHaveBeenCalledWith({
      page_offset: "1",
    });
  });

  it("removes the employer filter when its FilterMenuButton is clicked", () => {
    const user_leave_administrators = [
      createMockUserLeaveAdministrator({
        verified: true,
        employer_dba: "Acme Co",
      }),
    ];

    const { updateQuerySpy } = setup({
      query: {
        request_decision: "approved",
        employer_id: user_leave_administrators[0].employer_id,
      },
      userAttrs: {
        user_leave_administrators,
      },
    });

    userEvent.click(
      screen.getByRole("button", {
        name: `Remove filter: ${user_leave_administrators[0].employer_dba}`,
      })
    );

    expect(updateQuerySpy).toHaveBeenLastCalledWith({
      page_offset: "1",
      request_decision: "approved",
    });
  });

  it("updates the claim_status param when one of several status FilterMenuButtons is clicked", () => {
    const { updateQuerySpy } = setup({
      query: {
        claim_status: "Approved,Closed,Pending",
      },
    });

    userEvent.click(
      screen.getByRole("button", {
        name: `Remove filter: Closed`,
      })
    );

    expect(updateQuerySpy).toHaveBeenLastCalledWith({
      claim_status: "Approved,Pending",
      page_offset: "1",
    });
  });

  it("removes the claim_status param when the last remaining status FilterMenuButton is clicked", () => {
    const { updateQuerySpy } = setup({
      query: {
        claim_status: "Closed",
      },
    });

    userEvent.click(
      screen.getByRole("button", {
        name: `Remove filter: Closed`,
      })
    );

    expect(updateQuerySpy).toHaveBeenLastCalledWith({
      page_offset: "1",
    });
  });

  it("defaults to Sort by Status option", () => {
    setup();

    expect(screen.getByRole("combobox", { name: /sort/i })).toHaveValue(
      "absence_status,ascending"
    );
  });

  it("defaults to Sort by New applications option when is enabled", () => {
    process.env.featureFlags = JSON.stringify({
      employerShowMultiLeaveDashboard: true,
    });
    setup();

    expect(screen.getByRole("combobox", { name: /sort/i })).toHaveValue(
      "latest_follow_up_date,descending"
    );
  });

  it("updates order_by and order_direction params when a sort choice is selected", () => {
    const { updateQuerySpy } = setup();

    userEvent.selectOptions(screen.getByRole("combobox"), [
      "employee,ascending",
    ]);

    expect(updateQuerySpy).toHaveBeenCalledWith({
      order_by: "employee",
      order_direction: "ascending",
      page_offset: "1",
    });
  });

  // TODO (PORTAL-1560): Remove or update this test, once the deprecated table component is removed
  it("deprecated: renders Review By status", () => {
    const claims = [getClaim()];
    claims[0].managed_requirements = [
      {
        category: "",
        created_at: "",
        responded_at: "",
        type: "",
        status: "Open",
        follow_up_date: "2050-01-30",
      },
    ];

    const userAttrs = {
      user_leave_administrators: [verifiedUserLeaveAdministrator],
    };

    setup({ claims, userAttrs });

    expect(screen.getByText("Review by 1/30/2050")).toBeInTheDocument();
  });

  // TODO (PORTAL-1560): Remove  this test
  it("deprecated: renders status description section", () => {
    setup();

    expect(screen.getByText(/Status descriptions/)).toBeInTheDocument();
  });

  // TODO (PORTAL-1560): Remove  this test
  it("deprecated: does not render status description section when employerShowMultiLeaveDashboard is enabled", () => {
    process.env.featureFlags = JSON.stringify({
      employerShowMultiLeaveDashboard: true,
    });
    setup();

    expect(screen.queryByText(/Status descriptions/)).not.toBeInTheDocument();
  });
});
