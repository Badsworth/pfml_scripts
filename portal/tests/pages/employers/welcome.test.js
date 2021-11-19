import User, { UserLeaveAdministrator } from "../../../src/models/User";
import Welcome from "../../../src/pages/employers/welcome";
import { renderPage } from "../../test-utils";
import { screen } from "@testing-library/react";

describe("Employer welcome", () => {
  it("renders page", () => {
    const { container } = renderPage(Welcome);

    expect(container).toMatchSnapshot();
  });

  it("shows Verification alert when user has a verifiable employer", () => {
    renderPage(Welcome, {
      addCustomSetup: (appLogic) => {
        appLogic.users.user = new User({
          consented_to_data_sharing: true,
          email_address: "unique@miau.com",
          user_leave_administrators: [
            new UserLeaveAdministrator({
              has_verification_data: true,
              verified: false,
            }),
          ],
        });
      },
    });

    const alert = screen.getByRole("heading", {
      name: /Verify your account to continue/i,
    }).parentNode;

    expect(alert).toMatchSnapshot();
  });
});
