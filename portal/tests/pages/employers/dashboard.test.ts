import Claim, { ClaimEmployee } from "../../../src/models/Claim";
import { cleanup, screen, waitFor } from "@testing-library/react";
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
// @ts-expect-error Exists on the mock
import { getClaimsMock } from "../../../src/api/ClaimsApi";
import routes from "../../../src/routes";
import userEvent from "@testing-library/user-event";

// Avoid issue where USWDS generates unique ID each render,
// which causes havoc for our snapshot testing
// https://github.com/uswds/uswds/issues/4338

jest.mock("src/api/ClaimsApi");

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
    ...customAttrs,
  });
};

const setup = async (options?: {
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

    getClaimsMock.mockResolvedValue({
      claims: new ApiResourceCollection<Claim>("fineos_absence_id", claims),
      paginationMeta: {
        page_offset: 1,
        page_size: 25,
        total_pages: 3,
        total_records: 75,
        order_by: "created_at",
        order_direction: "ascending",
        ...paginationMeta,
      },
    });

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

  await waitForClaimsToLoad();

  return {
    updateQuerySpy,
    ...utils,
  };
};

async function waitForClaimsToLoad() {
  await waitFor(() => {
    expect(
      screen.queryByRole("progressbar", { name: /loading claims/i })
    ).not.toBeInTheDocument();
  });
}

describe("Employer dashboard", () => {
  beforeAll(() => {
    MockDate.set(MOCK_CURRENT_ISO_DATE);
  });

  it("renders the page with expected content and pagination components", async () => {
    const { container } = await setup();

    expect(container).toMatchSnapshot();
  });

  it("renders a table of claims, with links to status page", async () => {
    const claims = [
      getClaim({
        absence_periods: [
          createAbsencePeriod({
            request_decision: "Pending",
            absence_period_start_date: "2020-01-01",
            absence_period_end_date: "2020-02-01",
            reason: "Serious Health Condition - Employee",
            period_type: "Continuous",
          }),
        ],
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

    await setup({ claims, userAttrs });
    expect(screen.getByRole("table")).toMatchSnapshot();
  });

  it("renders '--' when a Claim's Employee name is blank", async () => {
    let claims = [getClaim()];
    claims = claims.map((claim) => {
      claim.employee = null;
      return claim;
    });

    await setup({
      claims,
      userAttrs: {
        user_leave_administrators: [verifiedUserLeaveAdministrator],
      },
    });

    expect(screen.getByRole("rowheader", { name: /--/ })).toBeInTheDocument();
  });

  it("renders Organization column only when user has more than one Employer", async () => {
    // Organization column should NOT show
    await setup({
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
    await setup({
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

  it("renders a 'no results' message in the table, and no pagination components when no claims are present", async () => {
    await setup({
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
  });

  // eslint-disable-next-line jest/no-focused-tests
  it("renders a verification message in the table, when all employers are unverified", async () => {
    await setup({
      userAttrs: {
        user_leave_administrators: [verifiableUserLeaveAdministrator],
      },
    });

    expect(
      screen.getByRole("cell", {
        name: /You have not verified any organizations/,
      })
    ).toMatchSnapshot();
  });

  it("renders only the pagination summary when only one page of claims exists", async () => {
    await setup({
      paginationMeta: {
        total_records: 25,
        total_pages: 1,
      },
    });

    expect(screen.getByText(/Viewing 1 to 25 of 25/i)).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /next/i })
    ).not.toBeInTheDocument();
  });

  it("changes the page_offset query param when a page navigation button is clicked", async () => {
    const { updateQuerySpy } = await setup({
      paginationMeta: {
        page_offset: 1,
        total_pages: 3,
      },
    });

    userEvent.click(screen.getByRole("button", { name: /next/i }));

    expect(updateQuerySpy).toHaveBeenCalledWith({
      page_offset: "2",
    });
  });

  it("renders the banner if there are any unverified employers", async () => {
    await setup({
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

  it("updates search param when a search is performed", async () => {
    const { updateQuerySpy } = await setup();

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

  it("clears search param when the search field is cleared", async () => {
    const { updateQuerySpy } = await setup({ query: { search: "Bud Baxter" } });

    userEvent.clear(screen.getByRole("textbox", { name: /search/i }));
    userEvent.click(screen.getByRole("button", { name: /search/i }));

    expect(updateQuerySpy).toHaveBeenCalledWith({
      page_offset: "1",
    });
  });

  it("sets initial filter form state from query prop", async () => {
    // Include multiple LA's so Employer filter shows
    const user_leave_administrators = [
      createMockUserLeaveAdministrator({
        verified: true,
      }),
      createMockUserLeaveAdministrator({
        verified: true,
      }),
    ];

    await setup({
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

  it("updates query params when user changes filter to Approved", async () => {
    const { updateQuerySpy } = await setup();

    userEvent.click(screen.getByRole("button", { name: /show filters/i }));
    userEvent.click(screen.getByRole("radio", { name: "Approved" }));
    userEvent.click(screen.getByRole("button", { name: /apply/i }));

    expect(updateQuerySpy).toHaveBeenCalledWith({
      request_decision: "approved",
      page_offset: "1",
    });
  });

  // eslint-disable-next-line jest/no-focused-tests
  it("resets query params when user clicks Reset action", async () => {
    const user_leave_administrators = [
      createMockUserLeaveAdministrator({
        verified: true,
      }),
      createMockUserLeaveAdministrator({
        verified: true,
      }),
    ];

    const { updateQuerySpy } = await setup({
      query: {
        request_decision: "approved",
        employer_id: user_leave_administrators[0].employer_id,
      },
      userAttrs: {
        user_leave_administrators,
      },
    });

    userEvent.click(screen.getByRole("button", { name: /show filters/i }));
    userEvent.click(screen.getByRole("button", { name: /reset/i }));

    expect(updateQuerySpy).toHaveBeenCalledWith({
      page_offset: "1",
    });
  });

  it("removes the employer filter when its FilterMenuButton is clicked", async () => {
    const user_leave_administrators = [
      createMockUserLeaveAdministrator({
        verified: true,
        employer_dba: "Acme Co",
      }),
    ];

    const { updateQuerySpy } = await setup({
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

  it("defaults to Sort by New applications option", async () => {
    await setup();

    expect(screen.getByRole("combobox", { name: /sort/i })).toHaveValue(
      "latest_follow_up_date,descending"
    );
  });

  it("updates order_by and order_direction params when a sort choice is selected", async () => {
    const { updateQuerySpy } = await setup();

    userEvent.selectOptions(screen.getByRole("combobox"), [
      "employee,ascending",
    ]);

    expect(updateQuerySpy).toHaveBeenCalledWith({
      order_by: "employee",
      order_direction: "ascending",
      page_offset: "1",
    });
  });
});
