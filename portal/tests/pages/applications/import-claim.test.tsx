import { screen, waitFor } from "@testing-library/react";
import ImportClaim from "../../../src/pages/applications/import-claim";
import User from "../../../src/models/User";
import { renderPage } from "../../test-utils";
import routes from "../../../src/routes";
import userEvent from "@testing-library/user-event";

const mfaScenarios = [
  // MFA enabled, phone number verified
  ["SMS", "***-***-1234", true],
  // MFA enabled, phone number NOT verified
  ["SMS", "***-***-1234", false],
  // MFA disabled, phone number verified
  ["Opt Out", "***-***-1234", true],
  // MFA preference not set, therefore phone number NOT verified
  [null, null, false],
] as const;

async function setup({
  phone_number_verified = false,
  userAttrs = {},
}: {
  phone_number_verified?: boolean;
  userAttrs?: Partial<User>;
} = {}) {
  const associateSpy = jest.fn();
  const invalidateApplicationsCacheSpy = jest.fn();
  const user = new User({
    consented_to_data_sharing: true,
    ...userAttrs,
  });

  let utils!: ReturnType<typeof renderPage>;
  // waitFor makes sure the async useEffect runs
  await waitFor(() => {
    utils = renderPage(ImportClaim, {
      pathname: routes.applications.importClaim,
      addCustomSetup: (appLogic) => {
        appLogic.auth.isPhoneVerified = jest
          .fn()
          .mockResolvedValueOnce(phone_number_verified);
        appLogic.users.user = user;
        appLogic.benefitsApplications.invalidateApplicationsCache =
          invalidateApplicationsCacheSpy;
        appLogic.applicationImports.associate = associateSpy;
      },
    });
  });

  return { ...utils, associateSpy, invalidateApplicationsCacheSpy };
}

describe("ImportClaim", () => {
  beforeEach(() => {
    process.env.featureFlags = JSON.stringify({
      channelSwitching: true,
    });
  });

  it("renders page not found when feature flag isn't enabled", async () => {
    process.env.featureFlags = JSON.stringify({ channelSwitching: false });
    await setup();

    expect(screen.getByText("Page not found")).toBeInTheDocument();
  });

  it("renders the page", async () => {
    const { container } = await setup();
    expect(container).toMatchSnapshot();
  });

  it.each(mfaScenarios)(
    "conditionally renders MFA alert based on MFA preference and phone verification (%s, %s, %s)",
    async (mfa_delivery_preference, _phone_number, phone_number_verified) => {
      await setup({
        phone_number_verified,
        userAttrs: {
          mfa_delivery_preference,
        },
      });

      const mfaAlert = screen.queryByText(/We need to verify your login/);

      if (mfa_delivery_preference !== "SMS" || !phone_number_verified) {
        expect(mfaAlert).toBeInTheDocument();
        expect(mfaAlert?.parentNode).toMatchSnapshot();
      } else {
        expect(mfaAlert).not.toBeInTheDocument();
      }
    }
  );

  it.each(mfaScenarios)(
    "renders read-only phone number and link regardless of MFA preference (%s, %s, %s)",
    async (mfa_delivery_preference, phone_number, phone_number_verified) => {
      await setup({
        phone_number_verified,
        userAttrs: {
          mfa_delivery_preference,
          mfa_phone_number: {
            int_code: "1",
            phone_number,
            phone_type: "Cell",
          },
        },
      });

      expect(
        screen.getByText(/Cell phone number/).parentNode
      ).toMatchSnapshot();
    }
  );

  it("invalidates the applications state, and submits data to API when user clicks submit", async () => {
    const { associateSpy, invalidateApplicationsCacheSpy } = await setup();

    userEvent.type(
      screen.getByRole("textbox", { name: /social security/i }),
      "123456789"
    );
    userEvent.type(
      screen.getByRole("textbox", { name: /application id/i }),
      "NTN-111-ABS-01"
    );
    expect(
      screen.queryByText("Submitting… Do not refresh or go back")
    ).not.toBeInTheDocument();
    userEvent.click(screen.getByRole("button", { name: "Add application" }));
    expect(
      screen.getByText("Submitting… Do not refresh or go back")
    ).toBeInTheDocument();

    expect(invalidateApplicationsCacheSpy).toHaveBeenCalled();

    await waitFor(() => {
      expect(associateSpy).toHaveBeenCalledWith({
        absence_case_id: "NTN-111-ABS-01",
        tax_identifier: "123-45-6789",
      });
    });
  });
});
