import { mockAuth, renderPage } from "../test-utils";
import { screen, waitFor } from "@testing-library/react";
import { AppLogic } from "../../src/hooks/useAppLogic";
import CreateAccount from "../../src/pages/create-account";
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
    const createAccount = jest.fn();
    const options = {
      isLoggedIn: false,
      addCustomSetup: (appLogicHook: AppLogic) => {
        appLogicHook.auth.createAccount = createAccount;
      },
    };
    renderPage(CreateAccount, options);
    userEvent.type(
      screen.getByRole("textbox", { name: "Email address" }),
      email
    );
    userEvent.type(screen.getByLabelText("Password"), password);
    userEvent.click(screen.getByRole("button", { name: "Create account" }));
    await waitFor(() => {
      expect(createAccount).toHaveBeenCalledWith(email, password);
    });
  });
});
