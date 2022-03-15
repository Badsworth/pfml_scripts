import User, { RoleDescription } from "../../../src/models/User";
import { act, screen } from "@testing-library/react";
import Settings from "../../../src/pages/user/settings";
import { renderPage } from "../../test-utils";
import routes from "../../../src/routes";
import tracker from "../../../src/services/tracker";
import userEvent from "@testing-library/user-event";

jest.mock("../../../src/services/tracker");

beforeEach(() => {
  process.env.featureFlags = JSON.stringify({ claimantShowMFA: true });
});

const updateUser = jest.fn();

const renderWithUser = (
  user = new User({
    email_address: "mock@gmail.com",
    consented_to_data_sharing: true,
  }),
  query: { [key: string]: string } = {}
) => {
  const props = {
    user,
    query,
  };
  return renderPage(
    Settings,
    {
      pathname: routes.user.settings,
      addCustomSetup: (appLogic) => {
        appLogic.users.user = user;
        appLogic.users.updateUser = updateUser;
      },
    },
    props
  );
};

describe(Settings, () => {
  it("renders the page", () => {
    const { container } = renderWithUser();
    expect(
      screen.getByText(/Additional login verification is not enabled/)
    ).toBeInTheDocument();
    expect(container).toMatchSnapshot();
  });

  describe("when MFA is enabled", () => {
    const user = new User({
      user_id: "mock-user-id",
      mfa_delivery_preference: "SMS",
      mfa_phone_number: {
        int_code: "1",
        phone_number: "***-***-1234",
        phone_type: "Cell",
      },
      email_address: "mock@gmail.com",
      consented_to_data_sharing: true,
    });

    it("shows MFA configuration", () => {
      const { container } = renderWithUser(user);
      expect(
        screen.getByText(/Additional login verification is enabled/)
      ).toBeInTheDocument();
      expect(container).toMatchSnapshot();
    });

    it("shows amendment form when user edits their login verification", async () => {
      renderWithUser(user);

      const editButton = screen.getAllByRole("button", { name: /Edit/ })[0];

      await act(async () => await userEvent.click(editButton));

      expect(
        await screen.findByText(/Edit login verification preferences/)
      ).toBeInTheDocument();
    });

    describe("and user is editing login verification", () => {
      beforeEach(async () => {
        renderWithUser(user);

        const editButton = screen.getAllByRole("button", { name: /Edit/ })[0];

        await act(async () => await userEvent.click(editButton));
      });

      it("hides amendment when user clicks cancel", async () => {
        const cancelButton = screen.getByRole("button", { name: /Cancel/ });
        await act(async () => await userEvent.click(cancelButton));

        expect(
          screen.queryByText(/Edit login verification preferences/)
        ).not.toBeInTheDocument();
      });

      it("changes radio value when user clicks an option", async () => {
        const disableRadio = screen.getByText(
          /Disable additional login verification/
        );
        await act(async () => await userEvent.click(disableRadio));
        expect(
          screen.getByLabelText(/Disable additional login verification/)
        ).toBeChecked();
        expect(
          screen.getByLabelText(/Enable additional login verification/)
        ).not.toBeChecked();

        const enableRadio = screen.getByText(
          /Enable additional login verification/
        );
        await act(async () => await userEvent.click(enableRadio));
        expect(
          screen.getByLabelText(/Disable additional login verification/)
        ).not.toBeChecked();
        expect(
          screen.getByLabelText(/Enable additional login verification/)
        ).toBeChecked();
      });

      it("saves mfa preference when user clicks save", async () => {
        const saveButton = screen.getByRole("button", {
          name: /Save preference/,
        });
        await act(async () => await userEvent.click(saveButton));

        expect(updateUser).toHaveBeenCalledWith(expect.any(String), {
          mfa_delivery_preference: "SMS",
        });
        expect(tracker.trackEvent).toHaveBeenCalledWith(
          "User kept MFA enabled"
        );
        expect(
          screen.queryByText(/Edit login verification preferences/)
        ).not.toBeInTheDocument();
      });

      it("tracks a user disabling MFA", async () => {
        const disableRadio = screen.getByText(
          /Disable additional login verification/
        );
        await act(async () => await userEvent.click(disableRadio));
        const saveButton = screen.getByRole("button", {
          name: /Save preference/,
        });
        await act(async () => await userEvent.click(saveButton));

        expect(updateUser).toHaveBeenCalledWith(expect.any(String), {
          mfa_delivery_preference: "Opt Out",
        });
        expect(tracker.trackEvent).toHaveBeenCalledWith("User disabled MFA");
      });
    });
  });

  it("displays success alert when user sets up SMS MFA", () => {
    renderPage(
      Settings,
      { pathname: routes.user.settings },
      { query: { smsMfaConfirmed: "true" } }
    );
    expect(screen.getByRole("region")).toMatchSnapshot();
  });

  it("renders 404 when claimantShowMFA feature flag is disabled", () => {
    process.env.featureFlags = JSON.stringify({ claimantShowMFA: false });
    renderPage(Settings, { pathname: routes.user.settings });

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });

  it("renders 404 when user has employer role", () => {
    const user = new User({
      user_id: "mock-user-id",
      mfa_delivery_preference: "SMS",
      mfa_phone_number: {
        int_code: "1",
        phone_number: "***-***-1234",
        phone_type: "Cell",
      },
      email_address: "mock@gmail.com",
      consented_to_data_sharing: true,
      roles: [{ role_description: RoleDescription.employer, role_id: 1 }],
    });
    renderWithUser(user);
    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });
});
