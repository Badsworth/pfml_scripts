import { screen, waitFor } from "@testing-library/react";
import FinishAccountSetup from "../../../src/pages/employers/finish-account-setup";
import { renderPage } from "../../test-utils";
import userEvent from "@testing-library/user-event";

describe("FinishAccountSetup", () => {
  it("renders the page", () => {
    const { container } = renderPage(FinishAccountSetup, { isLoggedIn: false });
    expect(container).toMatchSnapshot();
  });

  it("calls forgotPassword when the form is submitted", async () => {
    const spy = jest.fn();
    renderPage(FinishAccountSetup, {
      addCustomSetup: (appLogic) => {
        appLogic.auth.forgotPassword = spy;
      },
      isLoggedIn: false,
    });

    const email = "email@test.com";
    userEvent.type(screen.getByLabelText(/Email/i), email);
    userEvent.click(screen.getByRole("button", { name: /Submit/i }));

    await waitFor(() => {
      expect(spy).toHaveBeenCalledWith(email);
    });
  });
});
