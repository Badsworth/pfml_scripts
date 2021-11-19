import { mockAuth, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import CreateAccount from "../../../src/pages/employers/create-account";
import userEvent from "@testing-library/user-event";

describe("CreateAccount", () => {
  beforeEach(() => {
    mockAuth(false);
  });

  it("renders the empty page", () => {
    const { container } = renderPage(CreateAccount, { isLoggedIn: false });
    expect(container.firstChild).toMatchSnapshot();
  });

  it("calls createAccount when the form is submitted", async () => {
    const email = "email@test.com";
    const password = "TestP@ssw0rd!";
    const ein = "12-3456789";
    const createEmployerAccount = jest.fn();
    const options = {
      isLoggedIn: false,
      addCustomSetup: (appLogicHook) => {
        appLogicHook.auth.createEmployerAccount = createEmployerAccount;
      },
    };

    renderPage(CreateAccount, options);

    userEvent.type(
      screen.getByRole("textbox", { name: /Email address/i }),
      email
    );
    userEvent.type(screen.getByLabelText(/Password Your password/i), password);
    userEvent.type(screen.getByLabelText(/Employer ID number/i), ein);
    userEvent.click(screen.getByRole("button", { name: "Create account" }));

    await waitFor(() => {
      expect(createEmployerAccount).toHaveBeenCalledWith(email, password, ein);
    });
  });
});
