import { cleanup, screen, waitFor } from "@testing-library/react";
import ImportClaim from "../../../src/pages/applications/import-claim";
import User from "../../../src/models/User";
import { renderPage } from "../../test-utils";
import routes from "../../../src/routes";
import userEvent from "@testing-library/user-event";

function setup({
  userAttrs = {},
}: {
  userAttrs?: Partial<User>;
} = {}) {
  const associateSpy = jest.fn();
  const user = new User({
    consented_to_data_sharing: true,
    ...userAttrs,
  });

  const utils = renderPage(ImportClaim, {
    pathname: routes.applications.importClaim,
    addCustomSetup: (appLogic) => {
      appLogic.users.user = user;
      appLogic.benefitsApplications.associate = associateSpy;
    },
  });

  return { ...utils, associateSpy };
}

describe("ImportClaim", () => {
  beforeEach(() => {
    process.env.featureFlags = JSON.stringify({
      channelSwitching: true,
    });
  });

  it("renders page not found when feature flag isn't enabled", () => {
    process.env.featureFlags = JSON.stringify({ channelSwitching: false });
    setup();

    expect(screen.getByText("Page not found")).toBeInTheDocument();
  });

  it("renders the page", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("conditionally renders MFA alert based on user's MFA preference", () => {
    function findMfaAlert() {
      return screen.queryByText(/We need to verify your login/);
    }

    setup({
      userAttrs: {
        mfa_delivery_preference: "Opt Out",
      },
    });
    expect(findMfaAlert()).toBeInTheDocument();
    expect(findMfaAlert()?.parentNode).toMatchSnapshot();

    cleanup();

    setup({
      userAttrs: {
        mfa_delivery_preference: "SMS",
        mfa_phone_number: {
          int_code: "1",
          phone_number: "***-***-1234",
          phone_type: "Cell",
        },
      },
    });

    expect(findMfaAlert()).not.toBeInTheDocument();
  });

  it.each([
    ["SMS", "***-***-1234"],
    ["Opt Out", "***-***-1234"],
    [null, null],
  ] as const)(
    "renders read-only phone number and link regardless of MFA preference",
    (mfa_delivery_preference, phone_number) => {
      setup({
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

  it("associates application when user clicks submit", async () => {
    const { associateSpy } = setup();

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
    await waitFor(() => {
      expect(associateSpy).toHaveBeenCalledWith({
        absence_case_id: "NTN-111-ABS-01",
        tax_identifier: "123-45-6789",
      });
    });
  });
});
