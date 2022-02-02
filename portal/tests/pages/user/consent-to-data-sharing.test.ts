import User, { UserRole } from "../../../src/models/User";
import { screen, waitFor } from "@testing-library/react";
import ConsentToDataSharing from "../../../src/pages/user/consent-to-data-sharing";
import { renderPage } from "../../test-utils";
import tracker from "../../../src/services/tracker";
import userEvent from "@testing-library/user-event";

jest.mock("../../../src/hooks/useAppLogic");

// Return a user object to indicate a successful update
const updateUser = jest.fn().mockReturnValue(new User({}));
const portalGoToPage = jest.fn();

const renderWithUserParams = (
  user: Partial<User> = {
    user_id: "mock_user_id",
    consented_to_data_sharing: true,
  }
) => {
  return renderPage(ConsentToDataSharing, {
    addCustomSetup: (appLogic) => {
      appLogic.users.user = new User(user);
      appLogic.users.updateUser = updateUser;
      appLogic.portalFlow.goToPageFor = portalGoToPage;
    },
  });
};

beforeEach(() => {
  process.env.featureFlags = JSON.stringify({ claimantShowMFA: true });
});

describe("ConsentToDataSharing", () => {
  it("shows the correct content for non-employers", () => {
    const { container } = renderWithUserParams();
    expect(
      screen.getByRole("button", { name: "Applying for benefits" })
    ).toBeInTheDocument();
    expect(container).toMatchSnapshot();
  });

  it("shows the correct contents for employers", () => {
    const { container } = renderWithUserParams({
      user_id: "mock_user_id",
      consented_to_data_sharing: true,
      roles: [new UserRole({ role_description: "Employer" })],
    });

    expect(container).toMatchSnapshot();
    expect(
      screen.getByRole("button", { name: "Reviewing paid leave applications" })
    ).toBeInTheDocument();
  });

  it("on submit, we set user's consented_to_data_sharing field to true and track to new relic", async () => {
    const trackEventSpy = jest.spyOn(tracker, "trackEvent");
    renderWithUserParams();

    userEvent.click(screen.getByRole("button", { name: "Agree and continue" }));
    await waitFor(() => {
      expect(updateUser).toHaveBeenCalledWith("mock_user_id", {
        consented_to_data_sharing: true,
      });
      expect(trackEventSpy).toHaveBeenCalledWith(
        "User consented to data sharing",
        {}
      );
    });
  });

  it("on submit, it redirects to MFA setup page when user is not an Employer", async () => {
    renderWithUserParams();

    userEvent.click(screen.getByRole("button", { name: "Agree and continue" }));
    await waitFor(() => {
      expect(portalGoToPage).toHaveBeenCalledWith("ENABLE_MFA");
    });
  });

  it("on submit, it does not redirect to MFA setup page when user is an Employer", async () => {
    renderWithUserParams({
      user_id: "mock_user_id",
      consented_to_data_sharing: true,
      roles: [new UserRole({ role_description: "Employer" })],
    });

    userEvent.click(screen.getByRole("button", { name: "Agree and continue" }));
    await waitFor(() => {
      expect(portalGoToPage).not.toHaveBeenCalled();
    });
  });

  it("on submit, it does not redirect if we fail to update the user", async () => {
    renderWithUserParams();
    updateUser.mockImplementationOnce(() => undefined);

    await waitFor(async () => {
      await userEvent.click(
        screen.getByRole("button", { name: "Agree and continue" })
      );
    });
    expect(portalGoToPage).not.toHaveBeenCalled();
  });
});
