import User, { UserRole } from "../../../src/models/User";
import { screen, waitFor } from "@testing-library/react";
import ConsentToDataSharing from "../../../src/pages/user/consent-to-data-sharing";
import { renderPage } from "../../test-utils";
import tracker from "../../../src/services/tracker";
import userEvent from "@testing-library/user-event";

jest.mock("../../../src/hooks/useAppLogic");

const updateUser = jest.fn();

const renderWithUserParams = (user) => {
  if (!user) {
    user = { user_id: "mock_user_id", consented_to_data_sharing: true };
  }
  return renderPage(ConsentToDataSharing, {
    addCustomSetup: (appLogic) => {
      appLogic.users.user = new User(user);
      appLogic.users.updateUser = updateUser;
    },
  });
};

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
});
