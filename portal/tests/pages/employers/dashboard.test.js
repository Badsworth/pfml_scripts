import Claim, { ClaimEmployee, ClaimEmployer } from "../../../src/models/Claim";
import User, { UserLeaveAdministrator } from "../../../src/models/User";
import { renderWithAppLogic, testHook } from "../../test-utils";
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
      }),
      fineos_absence_id: "NTN-111-ABS-01",
      claim_status: "Approved",
    }),
  ];
};

const setup = (claims = [], userAttrs = {}, paginationMeta = {}) => {
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
  const goToSpy = jest.spyOn(appLogic.portalFlow, "goTo");

  const { wrapper } = renderWithAppLogic(Dashboard, {
    props: { appLogic },
    userAttrs,
  });

  return {
    appLogic,
    goToSpy,
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
    const { wrapper } = setup([], {
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
    const { wrapper } = setup([], {
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

  it("does not render a banner if there are any unverified employers that are not registered in FINEOS", () => {
    const { wrapper } = setup([], {
      user_leave_administrators: [verifiableUserLeaveAdministrator],
    });

    expect(wrapper.find("Alert").exists()).toEqual(false);
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

    const { wrapper } = setup(claims, userAttrs);

    expect(wrapper.find("ClaimTableRows").dive()).toMatchSnapshot();
    expect(wrapper.find("thead")).toMatchSnapshot();
  });

  it("renders claim rows without links if employer is not registered in FINEOS", () => {
    const claims = getClaims(verifiableUserLeaveAdministrator);

    const userAttrs = {
      user_leave_administrators: [verifiableUserLeaveAdministrator],
    };

    const { wrapper } = setup(claims, userAttrs);

    expect(wrapper.find("ClaimTableRows").dive().find("a")).toHaveLength(0);
  });

  it("allows Claim.employee to be null", () => {
    let claims = getClaims(verifiedUserLeaveAdministrator);
    claims = claims.map((claim) => {
      claim.employee = null;
      return claim;
    });

    const { wrapper } = setup(claims);

    expect(
      wrapper
        .find("ClaimTableRows")
        .dive()
        .find('[data-test="employee_name"]')
        .text()
    ).toBe("--");
  });

  it("does not render Employer DBA when user has only one Employer associated", () => {
    const { wrapper: soloEmployerWrapper } = setup([], {
      user_leave_administrators: [verifiedUserLeaveAdministrator],
    });
    const { wrapper: multipleEmployerWrapper } = setup([], {
      user_leave_administrators: [
        verifiedUserLeaveAdministrator,
        verifiableUserLeaveAdministrator,
      ],
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
    const { wrapper } = setup([], undefined, {
      total_records: 0,
      total_pages: 1,
    });

    expect(wrapper.find("ClaimTableRows").dive()).toMatchSnapshot();
    expect(wrapper.find("PaginationSummary").exists()).toBe(false);
    expect(wrapper.find("PaginationNavigation").exists()).toBe(false);
  });

  it("renders only the pagination summary when only one page of claims exists", () => {
    const { wrapper } = setup(undefined, undefined, {
      total_records: 25,
      total_pages: 1,
    });

    expect(wrapper.find("PaginationSummary").exists()).toBe(true);
    expect(wrapper.find("PaginationNavigation").exists()).toBe(false);
  });

  it("changes the page_offset query param when a page navigation button is clicked", () => {
    const { goToSpy, wrapper } = setup();
    const clickedPageOffset = "3";

    wrapper.find("PaginationNavigation").simulate("click", clickedPageOffset);

    expect(goToSpy).toHaveBeenCalledWith("/employers/dashboard", {
      page_offset: clickedPageOffset,
    });
  });

  describe("when employerShowVerifications flag is enabled", () => {
    beforeEach(() => {
      process.env.featureFlags = {
        ...process.env.featureFlags,
        employerShowVerifications: true,
      };
    });

    it("renders the banner if there are any unverified employers", () => {
      const { wrapper } = setup([], {
        user_leave_administrators: [
          // Mix of verified and unverified
          verifiedUserLeaveAdministrator,
          verifiableUserLeaveAdministrator,
        ],
      });
      expect(wrapper.find("Alert").exists()).toEqual(true);
    });

    it("renders instructions if there are no verified employers", () => {
      const { wrapper } = setup([], {
        // No verified employers
        user_leave_administrators: [verifiableUserLeaveAdministrator],
      });

      expect(
        wrapper.find("[data-test='verification-instructions-row'] Trans").dive()
      ).toMatchSnapshot();
    });
  });

  it("renders organizations filter when there are multiple verified organizations", () => {
    process.env.featureFlags = { employerShowDashboardEmployerFilter: true };

    const { wrapper: wrapperWithOneVerifiedOrg } = setup([], {
      user_leave_administrators: [
        createUserLeaveAdministrator({
          verified: false,
        }),
        createUserLeaveAdministrator({
          verified: true,
        }),
      ],
    });

    const { wrapper: wrapperWithMultipleVerifiedOrgs } = setup([], {
      user_leave_administrators: [
        createUserLeaveAdministrator({
          has_fineos_registration: false, // this should employer still show in the list
          verified: true,
        }),
        createUserLeaveAdministrator({
          has_fineos_registration: true,
          verified: true,
        }),
      ],
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

  it("updates filter + pagination query params when user selects an Employer filter", () => {
    process.env.featureFlags = { employerShowDashboardEmployerFilter: true };

    const user_leave_administrators = [
      createUserLeaveAdministrator({
        verified: true,
      }),
      createUserLeaveAdministrator({
        verified: true,
      }),
    ];

    const { goToSpy, wrapper } = setup(
      [],
      {
        user_leave_administrators,
      },
      {
        page_offset: 2,
      }
    );

    wrapper
      .find("Filters")
      .dive()
      .find("Dropdown[name='employer_id']")
      .simulate("change", {
        target: {
          name: "employer_id",
          value: user_leave_administrators[0].employer_id,
        },
      });

    expect(goToSpy).toHaveBeenCalledWith("/employers/dashboard", {
      employer_id: user_leave_administrators[0].employer_id,
      page_offset: "1",
    });
  });

  it("updates pagination query params when user selects the 'All organizations' Employer filter", () => {
    process.env.featureFlags = { employerShowDashboardEmployerFilter: true };

    const user_leave_administrators = [
      createUserLeaveAdministrator({
        verified: true,
      }),
      createUserLeaveAdministrator({
        verified: true,
      }),
    ];

    const { goToSpy, wrapper } = setup(
      [],
      {
        user_leave_administrators,
      },
      {
        page_offset: 2,
      }
    );

    const dropdown = wrapper
      .find("Filters")
      .dive()
      .find("Dropdown[name='employer_id']");

    dropdown.simulate("change", {
      target: {
        name: "employer_id",
        value: dropdown.prop("choices")[0].value, // All orgs = first option
      },
    });

    expect(goToSpy).toHaveBeenCalledWith("/employers/dashboard", {
      page_offset: "1",
    });
  });
});
