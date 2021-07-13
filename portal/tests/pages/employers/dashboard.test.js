import Claim, { ClaimEmployee, ClaimEmployer } from "../../../src/models/Claim";
import User, { UserLeaveAdministrator } from "../../../src/models/User";
import { renderWithAppLogic, simulateEvents, testHook } from "../../test-utils";
import ClaimCollection from "../../../src/models/ClaimCollection";
import Dashboard from "../../../src/pages/employers/dashboard";
import PaginationMeta from "../../../src/models/PaginationMeta";
import faker from "faker";
import { mockRouter } from "next/router";
import routes from "../../../src/routes";
import useAppLogic from "../../../src/hooks/useAppLogic";

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
      employer: new ClaimEmployer({
        employer_dba: leaveAdmin.employer_dba,
        employer_fein: leaveAdmin.employer_fein,
        employer_id: leaveAdmin.employer_id,
      }),
      fineos_absence_id: "NTN-111-ABS-01",
      claim_status: "Approved",
    }),
  ];
};

const setup = ({
  activeFilters = {},
  claims = [],
  userAttrs = {},
  paginationMeta = {},
  query = {},
} = {}) => {
  let appLogic;
  // Need to set an accurate pathname so portalFlow can return the correct links to route to
  mockRouter.pathname = routes.employers.dashboard;

  testHook(() => {
    appLogic = useAppLogic();
    // Fulfill the needs of withClaims to simulate that the user can view the page,
    // and that a list of claims has been loaded
    appLogic.users.user = new User({
      consented_to_data_sharing: true,
      ...userAttrs,
    });
    appLogic.claims.activeFilters = activeFilters;
    appLogic.claims.claims = new ClaimCollection(claims);
    appLogic.claims.shouldLoadPage = jest.fn().mockReturnValue(false);
    appLogic.claims.paginationMeta = new PaginationMeta({
      page_offset: 1,
      page_size: 25,
      total_pages: 3,
      total_records: 75,
      order_by: "created_at",
      order_direction: "asc",
      ...paginationMeta,
    });
  });
  const updateQuerySpy = jest.spyOn(appLogic.portalFlow, "updateQuery");

  const { wrapper } = renderWithAppLogic(Dashboard, {
    props: { appLogic, query },
    userAttrs,
  });

  return {
    appLogic,
    updateQuerySpy,
    wrapper,
  };
};

describe("Employer dashboard", () => {
  it("renders the page with expected content and pagination components", () => {
    const { wrapper } = setup();

    // Take targeted snapshots of content elements to avoid snapshotting noisy props
    expect(wrapper.find("Title")).toMatchSnapshot();
    wrapper.find("p").forEach((el) => expect(el).toMatchSnapshot());
    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());

    expect(wrapper.find("Details")).toMatchSnapshot();
    expect(wrapper.find("PaginationSummary")).toMatchSnapshot();
    expect(wrapper.find("PaginationNavigation")).toMatchSnapshot();
  });

  it("renders a beta info alert if all employers are registered in FINEOS", () => {
    const { wrapper } = setup({
      userAttrs: {
        user_leave_administrators: [
          new UserLeaveAdministrator({
            employer_dba: "Work Inc",
            employer_fein: "12-3456789",
            employer_id: "mock-employer-id-1",
            has_fineos_registration: true,
            has_verification_data: true,
            verified: true,
          }),
        ],
      },
    });

    expect(
      wrapper.find("DashboardInfoAlert").dive().find("Alert").prop("heading")
    ).toMatchInlineSnapshot(
      `"We're making it easier to manage paid leave applications"`
    );
    expect(
      wrapper.find("DashboardInfoAlert").dive().find("Alert Trans").dive()
    ).toMatchSnapshot();
  });

  it("renders an alert about claim availability when some employers aren't registered in FINEOS yet", () => {
    const { wrapper } = setup({
      userAttrs: {
        user_leave_administrators: [
          new UserLeaveAdministrator({
            employer_dba: "Work Inc",
            employer_fein: "12-3456789",
            employer_id: "mock-employer-id-1",
            has_fineos_registration: false,
            has_verification_data: true,
            verified: true,
          }),
          new UserLeaveAdministrator({
            employer_dba: "Work Co",
            employer_fein: "00-3456789",
            employer_id: "mock-employer-id-2",
            has_fineos_registration: false,
            has_verification_data: true,
            verified: true,
          }),
        ],
      },
    });

    expect(
      wrapper.find("DashboardInfoAlert").dive().find("Alert").prop("heading")
    ).toMatchInlineSnapshot(
      `"Your applications are not accessible right now for: 12-3456789, 00-3456789"`
    );

    expect(
      wrapper.find("DashboardInfoAlert").dive().find("Alert Trans").dive()
    ).toMatchSnapshot();
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

    const { wrapper } = setup({ claims, userAttrs });

    expect(wrapper.find("ClaimTableRows").dive()).toMatchSnapshot();
    expect(wrapper.find("thead")).toMatchSnapshot();
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

    const { wrapper } = setup({ claims, userAttrs });

    expect(wrapper.find("ClaimTableRows").dive().find("a")).toHaveLength(0);
  });

  it("allows Claim.employee to be null", () => {
    let claims = getClaims(verifiedUserLeaveAdministrator);
    claims = claims.map((claim) => {
      claim.employee = null;
      return claim;
    });

    const { wrapper } = setup({
      claims,
      userAttrs: {
        user_leave_administrators: [verifiedUserLeaveAdministrator],
      },
    });

    expect(
      wrapper
        .find("ClaimTableRows")
        .dive()
        .find('[data-test="employee_name"] a')
        .text()
    ).toBe("--");
  });

  it("does not render Employer DBA when user has only one Employer associated", () => {
    const { wrapper: soloEmployerWrapper } = setup({
      userAttrs: {
        user_leave_administrators: [verifiedUserLeaveAdministrator],
      },
    });
    const { wrapper: multipleEmployerWrapper } = setup({
      userAttrs: {
        user_leave_administrators: [
          verifiedUserLeaveAdministrator,
          verifiableUserLeaveAdministrator,
        ],
      },
    });

    expect(soloEmployerWrapper.find("ClaimTableRows").prop("tableColumnKeys"))
      .toMatchInlineSnapshot(`
      Array [
        "employee_name",
        "fineos_absence_id",
        "employer_fein",
        "created_at",
        "status",
      ]
    `);
    expect(
      multipleEmployerWrapper.find("ClaimTableRows").prop("tableColumnKeys")
    ).toMatchInlineSnapshot(`
      Array [
        "employee_name",
        "fineos_absence_id",
        "employer_dba",
        "employer_fein",
        "created_at",
        "status",
      ]
    `);
  });

  it("renders a 'no results' message in the table, and no pagination components when no claims are present", () => {
    const { wrapper } = setup({
      userAttrs: {
        user_leave_administrators: [verifiedUserLeaveAdministrator],
      },
      paginationMeta: {
        total_records: 0,
        total_pages: 1,
      },
    });

    expect(wrapper.find("ClaimTableRows").dive()).toMatchSnapshot();
    expect(wrapper.find("PaginationSummary").exists()).toBe(false);
    expect(wrapper.find("PaginationNavigation").exists()).toBe(false);
  });

  it("renders only the pagination summary when only one page of claims exists", () => {
    const { wrapper } = setup({
      paginationMeta: {
        total_records: 25,
        total_pages: 1,
      },
    });

    expect(wrapper.find("PaginationSummary").exists()).toBe(true);
    expect(wrapper.find("PaginationNavigation").exists()).toBe(false);
  });

  it("changes the page_offset query param when a page navigation button is clicked", () => {
    const { updateQuerySpy, wrapper } = setup();
    const clickedPageOffset = "3";

    wrapper.find("PaginationNavigation").simulate("click", clickedPageOffset);

    expect(updateQuerySpy).toHaveBeenCalledWith({
      page_offset: clickedPageOffset,
    });
  });

  it("renders the banner if there are any unverified employers", () => {
    const { wrapper } = setup({
      userAttrs: {
        user_leave_administrators: [
          // Mix of verified and unverified
          verifiedUserLeaveAdministrator,
          verifiableUserLeaveAdministrator,
        ],
      },
    });
    expect(wrapper.find("Alert").exists()).toEqual(true);
  });

  it("renders instructions if there are no verified employers", () => {
    const { wrapper } = setup({
      userAttrs: {
        // No verified employers
        user_leave_administrators: [verifiableUserLeaveAdministrator],
      },
    });

    expect(
      wrapper.find("[data-test='verification-instructions-row'] Trans").dive()
    ).toMatchSnapshot();
  });

  it("does not render search section when no search feature flag is enabled", () => {
    const { wrapper } = setup();

    expect(wrapper.find("Search").dive().isEmptyRender()).toBe(true);
  });

  it("renders search section when feature flags are enabled", () => {
    process.env.featureFlags = {
      employerShowDashboardSearch: true,
    };

    const { wrapper } = setup({
      activeFilters: {
        search: "Initial search field value",
      },
    });

    expect(wrapper.find("Search").dive()).toMatchSnapshot();
  });

  it("updates search param when a search is performed", async () => {
    process.env.featureFlags = {
      employerShowDashboardSearch: true,
    };

    const { updateQuerySpy, wrapper } = setup();

    const search = wrapper.find("Search").dive();
    const { changeField, submitForm } = simulateEvents(search);

    changeField("search", "Bud Baxter");
    await submitForm();

    expect(updateQuerySpy).toHaveBeenCalledWith({
      page_offset: "1",
      search: "Bud Baxter",
    });
  });

  it("does not render filters when no filter feature flags are enabled", () => {
    const { wrapper } = setup();

    expect(wrapper.find("Filters").dive().isEmptyRender()).toBe(true);
  });

  it("renders filters when feature flags are enabled", () => {
    process.env.featureFlags = {
      employerShowDashboardFilters: true,
    };

    const { wrapper } = setup({
      userAttrs: {
        // Include multiple LA's so Employer filter shows
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

    expect(wrapper.find("Filters").dive()).toMatchSnapshot();
  });

  it("renders filters toggle button with expected label and aria attributes", () => {
    process.env.featureFlags = {
      employerShowDashboardFilters: true,
    };

    const user_leave_administrators = [
      createUserLeaveAdministrator({
        verified: true,
      }),
    ];
    const { wrapper: CollapsedWithoutFilters } = setup();
    const { wrapper: CollapsedWithFilters } = setup({
      activeFilters: {
        claim_status: "Pending",
        employer_id: user_leave_administrators[0].employer_id,
      },
      userAttrs: {
        // Include multiple LA's so Employer filter shows
        user_leave_administrators,
      },
    });
    const { wrapper: ExpandedWithoutFilters } = setup({
      query: {
        "show-filters": "true",
      },
    });

    const getButton = (w) =>
      w.find("Filters").dive().find("Button[aria-controls='filters']");

    expect(getButton(CollapsedWithFilters)).toMatchSnapshot();
    expect(getButton(CollapsedWithoutFilters)).toMatchSnapshot();
    expect(getButton(ExpandedWithoutFilters)).toMatchSnapshot();
  });

  it("sets initial filter form state from activeFilters prop", () => {
    process.env.featureFlags = {
      employerShowDashboardFilters: true,
    };
    // Include multiple LA's so Employer filter shows
    const user_leave_administrators = [
      createUserLeaveAdministrator({
        verified: true,
      }),
      createUserLeaveAdministrator({
        verified: true,
      }),
    ];

    const { wrapper } = setup({
      activeFilters: {
        claim_status: "Approved,Closed",
        employer_id: user_leave_administrators[0].employer_id,
      },
      userAttrs: {
        user_leave_administrators,
      },
    });

    const filters = wrapper.find("Filters").dive();

    expect(filters.find("Dropdown").prop("value")).toBe(
      user_leave_administrators[0].employer_id
    );
    expect(
      filters
        .find("InputChoiceGroup")
        .prop("choices")
        .map((choice) => choice.checked)
    ).toMatchInlineSnapshot(`
      Array [
        true,
        true,
        false,
        false,
      ]
    `);
  });

  it("shows filters section when show-filters query param is set", () => {
    process.env.featureFlags = {
      employerShowDashboardFilters: true,
    };

    const { wrapper: collapsedWrapper } = setup();
    const { wrapper: expandedWrapper } = setup({
      query: {
        "show-filters": "true",
      },
    });

    const getFiltersContainer = (w) =>
      w.find("Filters").dive().find("#filters");

    expect(getFiltersContainer(collapsedWrapper).prop("hidden")).toBe(true);
    expect(getFiltersContainer(expandedWrapper).prop("hidden")).toBe(false);
  });

  it("toggles show-filters param when toggle button is clicked", () => {
    process.env.featureFlags = {
      employerShowDashboardFilters: true,
    };

    const { updateQuerySpy, wrapper } = setup();
    const filters = wrapper.find("Filters").dive();
    const { click } = simulateEvents(filters);

    click("Button[aria-controls='filters']");

    expect(updateQuerySpy).toHaveBeenCalledWith({ "show-filters": "true" });
  });

  it("renders organizations filter when there are multiple verified organizations", () => {
    process.env.featureFlags = { employerShowDashboardFilters: true };

    const { wrapper: wrapperWithOneVerifiedOrg } = setup({
      userAttrs: {
        user_leave_administrators: [
          createUserLeaveAdministrator({
            verified: false,
          }),
          createUserLeaveAdministrator({
            verified: true,
          }),
        ],
      },
    });

    const { wrapper: wrapperWithMultipleVerifiedOrgs } = setup({
      userAttrs: {
        user_leave_administrators: [
          createUserLeaveAdministrator({
            has_fineos_registration: false, // this employer should still show in the list
            verified: true,
          }),
          createUserLeaveAdministrator({
            has_fineos_registration: true,
            verified: true,
          }),
        ],
      },
    });

    const getEmployerFilterDropdown = (wrapper) =>
      wrapper.find("Filters").dive().find("Dropdown[name='employer_id']");

    expect(getEmployerFilterDropdown(wrapperWithOneVerifiedOrg).exists()).toBe(
      false
    );
    expect(
      getEmployerFilterDropdown(wrapperWithMultipleVerifiedOrgs).exists()
    ).toBe(true);
  });

  it("updates query params when user changes filter to Approved and Closed", async () => {
    expect.assertions();

    process.env.featureFlags = {
      employerShowDashboardFilters: true,
    };

    const user_leave_administrators = [
      createUserLeaveAdministrator({
        verified: true,
      }),
      createUserLeaveAdministrator({
        verified: true,
      }),
    ];

    const { updateQuerySpy, wrapper } = setup({
      userAttrs: {
        user_leave_administrators,
      },
      paginationMeta: {
        page_offset: 2,
      },
    });

    const filtersWrapper = wrapper.find("Filters").dive();
    const { changeField, changeCheckbox, submitForm } = simulateEvents(
      filtersWrapper
    );

    changeCheckbox("claim_status", true, "Approved");
    changeCheckbox("claim_status", true, "Closed");
    changeField("employer_id", user_leave_administrators[0].employer_id);

    expect(filtersWrapper.find("Button[type='submit']").prop("disabled")).toBe(
      false
    );

    await submitForm();
    expect(updateQuerySpy).toHaveBeenCalledWith({
      claim_status: "Approved,Closed",
      employer_id: user_leave_administrators[0].employer_id,
      page_offset: "1",
    });
  });

  it("resets query params when user clicks Reset action", () => {
    process.env.featureFlags = {
      employerShowDashboardFilters: true,
    };

    const user_leave_administrators = [
      createUserLeaveAdministrator({
        verified: true,
      }),
      createUserLeaveAdministrator({
        verified: true,
      }),
    ];

    const { updateQuerySpy, wrapper } = setup({
      activeFilters: {
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

    const filtersWrapper = wrapper.find("Filters").dive();
    const { click } = simulateEvents(filtersWrapper);

    click("Button[data-test='reset-filters']");

    expect(updateQuerySpy).toHaveBeenCalledWith({
      page_offset: "1",
    });
  });

  it("shows buttons for removing active filters", () => {
    const user_leave_administrators = [
      createUserLeaveAdministrator({
        verified: true,
        employer_dba: "Acme Co",
      }),
    ];

    const { wrapper: wrapperWithActiveFilters } = setup({
      activeFilters: {
        claim_status: "Approved,Closed",
        employer_id: user_leave_administrators[0].employer_id,
      },
      userAttrs: {
        user_leave_administrators,
      },
    });
    const { wrapper: wrapperWithoutActiveFilters } = setup({
      userAttrs: {
        user_leave_administrators,
      },
    });

    const findFiltersMenu = (wrapper) =>
      wrapper.find("Filters").dive().find("[data-test='filters-menu']");

    expect(findFiltersMenu(wrapperWithoutActiveFilters).exists()).toBe(false);
    expect(findFiltersMenu(wrapperWithActiveFilters)).toMatchSnapshot();
  });

  it("removes filter when a filter menu button is clicked", () => {
    const user_leave_administrators = [
      createUserLeaveAdministrator({
        verified: true,
        employer_dba: "Acme Co",
      }),
    ];

    const { updateQuerySpy, wrapper } = setup({
      activeFilters: {
        claim_status: "Approved,Closed",
        employer_id: user_leave_administrators[0].employer_id,
      },
      userAttrs: {
        user_leave_administrators,
      },
    });
    const { click } = simulateEvents(wrapper.find("Filters").dive());

    click("FilterMenuButton[data-test='employer_id']");
    expect(updateQuerySpy).toHaveBeenLastCalledWith({
      page_offset: "1",
    });

    click("FilterMenuButton[data-test='claim_status_Closed']");
    expect(updateQuerySpy).toHaveBeenLastCalledWith({
      claim_status: "Approved",
      page_offset: "1",
    });
  });
});
