import { MockEmployerClaimBuilder, renderWithAppLogic } from "../../test-utils";
import Dashboard from "../../../src/pages/employers/dashboard";
import { UserLeaveAdministrator } from "../../../src/models/User";
import routes from "../../../src/routes";

jest.mock("../../../src/hooks/useAppLogic");

const verifiedUserLeaveAdministrator = new UserLeaveAdministrator({
  employer_dba: "Acme Co",
  employer_fein: "**-***0001",
  employer_id: "mock-employer-id-1",
  has_verification_data: true,
  verified: true,
});
const verifiableUserLeaveAdministrator = new UserLeaveAdministrator({
  employer_dba: "Book Bindings 'R Us",
  employer_fein: "**-***0002",
  employer_id: "mock-employer-id-2",
  has_verification_data: true,
  verified: false,
});

const setup = (claims = [], userAttrs = {}) => {
  const { appLogic, wrapper } = renderWithAppLogic(Dashboard, {
    diveLevels: 1,
    props: { claims },
    userAttrs,
  });

  return {
    appLogic,
    wrapper,
  };
};

describe("Employer dashboard", () => {
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

  it("renders a table of claims", () => {
    const claims = [
      new MockEmployerClaimBuilder().completed().create(),
      new MockEmployerClaimBuilder().completed().create(),
    ];
    const userAttrs = {
      // Set multiple employers so the table shows all possible columns
      user_leave_administrators: [
        verifiedUserLeaveAdministrator,
        verifiableUserLeaveAdministrator,
      ],
    };
    const { wrapper } = setup(claims, userAttrs);

    expect(wrapper.find("ClaimTableRows").dive()).toMatchSnapshot();
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
    const { appLogic } = setup();

    expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
      routes.employers.welcome
    );
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
