import Settings from "../../../src/pages/user/settings";
import User from "../../../src/models/User";
import { renderPage } from "../../test-utils";
import { screen } from "@testing-library/react";

beforeEach(() => {
  process.env.featureFlags = { claimantShowMFA: true };
});

describe(Settings, () => {
  it("renders the page", () => {
    const { container } = renderPage(Settings, {
      addCustomSetup: (appLogic) => {
        appLogic.users.user = new User({
          email_address: "mock@gmail.com",
          consented_to_data_sharing: true,
        });
      },
    });
    expect(
      screen.getByText(/Additional login verification is not enabled/)
    ).toBeInTheDocument();
    expect(container).toMatchSnapshot();
  });

  it("shows mfa configuration when MFA is enabled", () => {
    const { container } = renderPage(Settings, {
      addCustomSetup: (appLogic) => {
        appLogic.users.user = new User({
          mfa_delivery_preference: "SMS",
          mfa_phone_number: {
            int_code: "1",
            phone_type: "Cell",
            phone_number: "***-***-1234",
          },
          email_address: "mock@gmail.com",
          consented_to_data_sharing: true,
        });
      },
    });
    expect(
      screen.getByText(/Additional login verification is enabled/)
    ).toBeInTheDocument();
    expect(container).toMatchSnapshot();
  });

  it("renders 404 when claimantShowMFA feature flag is disabled", () => {
    process.env.featureFlags = { claimantShowMFA: false };
    renderPage(Settings);

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });
});
