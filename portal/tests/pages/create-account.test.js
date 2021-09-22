import { screen, waitFor } from "@testing-library/react";
import CreateAccount from "../../src/pages/create-account";
import { renderPage } from "../test-utils";
import userEvent from "@testing-library/user-event";

jest.mock("../../src/hooks/useAppLogic");
jest.mock("../../src/hooks/useLoggedInRedirect");

describe("CreateAccount", () => {
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
      addCustomSetup: (appLogicHook) => {
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
