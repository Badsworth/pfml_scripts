import Claim, { ClaimEmployee, ClaimEmployer } from "../../../src/models/Claim";
import User, { UserLeaveAdministrator } from "../../../src/models/User";
import { renderWithAppLogic, testHook } from "../../test-utils";
import ClaimCollection from "../../../src/models/ClaimCollection";
import Dashboard from "../../../src/pages/employers/dashboard";
import { mockRouter } from "next/router";
import routes from "../../../src/routes";
import useAppLogic from "../../../src/hooks/useAppLogic";

const verifiedUserLeaveAdministrator = new UserLeaveAdministrator({
  employer_dba: "Work Inc",
  employer_fein: "12-3456789",
  employer_id: "mock-employer-id-1",
  has_fineos_registration: true,
  has_verification_data: true,
  verified: true,
});
const verifiableUserLeaveAdministrator = new UserLeaveAdministrator({
  employer_dba: "Book Bindings 'R Us",
  employer_fein: "**-***0002",
  employer_id: "mock-employer-id-2",
  has_fineos_registration: false,
  has_verification_data: true,
  verified: false,
});

const setup = (claims = [], userAttrs = {}) => {
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
    appLogic.claims.hasLoadedAll = true;
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
        fineos_absence_status: "Approved",
      }),
    ];
  };

  beforeEach(() => {
    process.env.featureFlags = { employerShowDashboard: true };
  });

  it("renders the page", () => {
    const { wrapper } = setup();

    // Take targeted snapshots of content elements to avoid snapshotting noisy props
    expect(wrapper.find("Title")).toMatchSnapshot();
    wrapper.find("p").forEach((el) => expect(el).toMatchSnapshot());
    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });

  it("renders a banner if there are any employers not registered in FINEOS", () => {
    const { wrapper } = setup([], {
      user_leave_administrators: [
        // Mix of registered and pending
        verifiedUserLeaveAdministrator,
        verifiableUserLeaveAdministrator,
      ],
    });

    expect(wrapper.find("Alert").prop("heading")).toMatchInlineSnapshot(
      `"Your applications are not accessible at the moment"`
    );
    expect(wrapper.find("Alert").dive().find("Trans").dive()).toMatchSnapshot();
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
    expect(wrapper.find("ClaimTableRows").dive().find("a")).toHaveLength(2);
  });

  it("renders claim rows without links if employer is not registered in FINEOS", () => {
    const claims = getClaims(verifiableUserLeaveAdministrator);

    const userAttrs = {
      user_leave_administrators: [verifiableUserLeaveAdministrator],
    };

    const { wrapper } = setup(claims, userAttrs);

    expect(wrapper.find("ClaimTableRows").dive()).toMatchSnapshot();
    expect(wrapper.find("ClaimTableRows").dive().find("a")).toHaveLength(0);
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

  it("renders a 'no results' message in the table if no claims are present", () => {
    const { wrapper } = setup([]);

    expect(wrapper.find("ClaimTableRows").dive()).toMatchSnapshot();
  });

  it("redirects to the Welcome page when employerShowDashboard flag is disabled", () => {
    process.env.featureFlags = { employerShowDashboard: false };
    const { goToSpy } = setup();

    expect(goToSpy).toHaveBeenCalledWith(routes.employers.welcome);
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
});
