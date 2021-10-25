import Claim, { ClaimEmployee } from "../../../src/models/Claim";
import User, { UserLeaveAdministrator } from "../../../src/models/User";
import { cleanup, screen, within } from "@testing-library/react";
import ClaimCollection from "../../../src/models/ClaimCollection";
import Dashboard from "../../../src/pages/employers/dashboard";
import PaginationMeta from "../../../src/models/PaginationMeta";
import faker from "faker";
import { mockRouter } from "next/router";
import { renderPage } from "../../test-utils";
import routes from "../../../src/routes";
import userEvent from "@testing-library/user-event";

// Avoid issue where USWDS generates unique ID each render,
// which causes havoc for our snapshot testing
// https://github.com/uswds/uswds/issues/4338
jest.mock("../../../src/components/TooltipIcon", () => ({
  __esModule: true,
  default: () => null,
}));

function createUserLeaveAdministrator(attrs = {}) {
  return new UserLeaveAdministrator({
    employer_id: faker.datatype.uuid(),
    employer_dba: faker.company.companyName(),
    employer_fein: `${faker.finance.account(2)}-${faker.finance.account(7)}`,
    ...attrs,
  });
}

const verifiedUserLeaveAdministrator = createUserLeaveAdministrator({
  employer_dba: "Work Inc",
  employer_fein: "12-3456789",
  has_fineos_registration: true,
  has_verification_data: true,
  verified: true,
});

const verifiableUserLeaveAdministrator = createUserLeaveAdministrator({
  employer_dba: "Book Bindings 'R Us",
  has_fineos_registration: false,
  has_verification_data: true,
  verified: false,
});

const getClaims = (leaveAdmin) => {
  return [
    new Claim({
      created_at: "2021-01-15",
      employee: new ClaimEmployee({
        first_name: "Jane",
        middle_name: null,
        last_name: "Doe",
      }),
      employer: {
        employer_dba: leaveAdmin.employer_dba,
        employer_fein: leaveAdmin.employer_fein,
        employer_id: leaveAdmin.employer_id,
      },
      fineos_absence_id: "NTN-111-ABS-01",
      claim_status: "Approved",
    }),
  ];
};

const setup = ({
  claims = [],
  userAttrs = {},
  paginationMeta = {},
  query = {},
} = {}) => {
  let updateQuerySpy;

  // Need to set an accurate pathname so portalFlow can return the correct links to route to
  mockRouter.pathname = routes.employers.dashboard;

  // Need to manually set window.location so that we can set the active query string
  delete window.location;
  window.location = { search: `?${new URLSearchParams(query)}` };

  const setupAppLogic = (appLogic) => {
    // Fulfill the needs of withClaims to simulate that the user can view the page,
    // and that a list of claims has been loaded
    appLogic.users.user = new User({
      consented_to_data_sharing: true,
      ...userAttrs,
    });
    appLogic.claims.claims = new ClaimCollection(claims);
    appLogic.claims.shouldLoadPage = jest.fn().mockReturnValue(false);
    appLogic.claims.isLoadingClaims = false;
    appLogic.claims.paginationMeta = new PaginationMeta({
      page_offset: 1,
      page_size: 25,
      total_pages: 3,
      total_records: 75,
      order_by: "created_at",
      order_direction: "asc",
      ...paginationMeta,
    });

    updateQuerySpy = jest.spyOn(appLogic.portalFlow, "updateQuery");
  };

  const utils = renderPage(
    Dashboard,
    {
      addCustomSetup: setupAppLogic,
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
  it("renders the page with expected content and pagination components", () => {
    const { container } = setup();

    expect(container).toMatchSnapshot();
  });

  it("renders a table of claims with links if employer is registered in FINEOS", () => {
    const claims = getClaims(verifiedUserLeaveAdministrator);
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

  it("renders claim rows without links if employer is not registered in FINEOS", () => {
    const verifiedButNotInFineos = {
      ...verifiableUserLeaveAdministrator,
      verified: true,
    };
    const claims = getClaims(verifiedButNotInFineos);

    const userAttrs = {
      user_leave_administrators: [verifiedButNotInFineos],
    };

    setup({ claims, userAttrs });
    expect(
      within(screen.getByRole("table")).queryByRole("link")
    ).not.toBeInTheDocument();
  });

  it("renders '--' when a Claim's Employee name is blank", () => {
    let claims = getClaims(verifiedUserLeaveAdministrator);
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

    expect(screen.getByRole("rowheader", { name: "--" })).toBeInTheDocument();
  });

  it("renders Organization column only when user has more than one Employer", () => {
    // Organization column should NOT
    setup({
      userAttrs: {
        user_leave_administrators: [verifiedUserLeaveAdministrator],
      },
    });

    expect(screen.getAllByRole("columnheader").map((el) => el.textContent))
      .toMatchInlineSnapshot(`
      Array [
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
      Array [
        "Employee name",
        "Application ID",
        "Organization",
        "Employer ID number",
        "Application start date",
        "Status",
      ]
    `);
  });

  it("renders a 'no results' message in the table, and no pagination components when no claims are present", () => {
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
  });

  it("renders only the pagination summary when only one page of claims exists", () => {
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
  });

  it("changes the page_offset query param when a page navigation button is clicked", () => {
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
  });

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

  it("displays number of active filters in Show Filters button", () => {
    const user_leave_administrators = [
      createUserLeaveAdministrator({
        verified: true,
      }),
    ];
    setup({
      query: {
        claim_status: "Pending",
        employer_id: user_leave_administrators[0].employer_id,
      },
      userAttrs: {
        // Include multiple LA's so Employer filter shows
        user_leave_administrators,
      },
    });

    expect(
      screen.getByRole("button", { name: "Show filters (2)" })
    ).toBeInTheDocument();
  });

  it("toggles filters visibility when Show Filters button is clicked", () => {
    setup();
    const toggleButton = screen.getByRole("button", { name: "Show filters" });

    // Collapsed by default
    expect(
      screen.queryByRole("group", { name: /status/i })
    ).not.toBeInTheDocument();

    // Show the filters
    userEvent.click(toggleButton);

    expect(toggleButton).toHaveAccessibleName("Hide filters");
    expect(
      screen.queryByRole("group", { name: /status/i })
    ).toBeInTheDocument();
  });

  it("sets initial filter form state from query prop", () => {
    // Include multiple LA's so Employer filter shows
    const user_leave_administrators = [
      createUserLeaveAdministrator({
        verified: true,
      }),
      createUserLeaveAdministrator({
        verified: true,
      }),
    ];

    setup({
      query: {
        claim_status: "Approved,Closed",
        employer_id: user_leave_administrators[0].employer_id,
      },
      userAttrs: {
        user_leave_administrators,
      },
    });

    userEvent.click(screen.getByRole("button", { name: /Show filters/i }));

    expect(
      screen.getByRole("combobox", { name: /organizations/i }).value
    ).toMatch(user_leave_administrators[0].employer_dba);
    expect(screen.getByRole("checkbox", { name: /approved/i })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /closed/i })).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /denied/i })).not.toBeChecked();
  });

  it("renders organizations filter when there are multiple verified organizations", () => {
    setup({
      userAttrs: {
        user_leave_administrators: [
          createUserLeaveAdministrator({
            employer_dba: "Work Inc",
            employer_id: "mock-id-1",
            employer_fein: "11-3456789",
            verified: true,
          }),
          createUserLeaveAdministrator({
            employer_dba: "Acme",
            employer_id: "mock-id-2",
            employer_fein: "22-3456789",
            verified: true,
          }),
        ],
      },
    });

    userEvent.click(screen.getByRole("button", { name: /show filters/i }));

    expect(
      screen.getByRole("combobox", { name: /organizations/i })
    ).toBeInTheDocument();
  });

  it("updates query params when user changes filter to Approved and Closed", () => {
    const { updateQuerySpy } = setup({
      paginationMeta: {
        page_offset: 2,
      },
    });

    userEvent.click(screen.getByRole("button", { name: /show filters/i }));
    userEvent.click(screen.getByRole("checkbox", { name: "Approved" }));
    userEvent.click(screen.getByRole("checkbox", { name: "Closed" }));
    userEvent.click(screen.getByRole("button", { name: /apply/i }));

    expect(updateQuerySpy).toHaveBeenCalledWith({
      claim_status: "Approved,Closed",
      page_offset: "1",
    });
  });

  it("resets query params when user clicks Reset action", () => {
    const user_leave_administrators = [
      createUserLeaveAdministrator({
        verified: true,
      }),
      createUserLeaveAdministrator({
        verified: true,
      }),
    ];

    const { updateQuerySpy } = setup({
      query: {
        claim_status: "Approved",
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
      createUserLeaveAdministrator({
        verified: true,
        employer_dba: "Acme Co",
      }),
    ];

    const { updateQuerySpy } = setup({
      query: {
        claim_status: "Approved,Closed",
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
      claim_status: "Approved,Closed",
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

  it("defaults to Sort by Status option when Review By feature flag is enabled", () => {
    process.env.featureFlags = {
      employerShowReviewByStatus: true,
    };

    setup();

    expect(screen.getByRole("combobox", { name: /sort/i })).toHaveValue(
      "absence_status,ascending"
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

  it("renders Review By status when feature flag is enabled", () => {
    process.env.featureFlags = {
      employerShowReviewByStatus: true,
    };

    const claims = getClaims(verifiedUserLeaveAdministrator);
    claims[0].managed_requirements = [
      {
        follow_up_date: "2050-01-30",
      },
    ];

    const userAttrs = {
      user_leave_administrators: [verifiedUserLeaveAdministrator],
    };

    setup({ claims, userAttrs });

    expect(screen.getByText("Review by 1/30/2050")).toBeInTheDocument();
  });
});
