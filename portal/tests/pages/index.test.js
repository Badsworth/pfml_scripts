import { screen, waitFor } from "@testing-library/react";
import { Auth } from "@aws-amplify/auth";
import Index from "../../src/pages/index";
import { renderPage } from "../test-utils";

jest.mock("../../src/hooks/useAppLogic");

describe("Index", () => {
  const options = { isLoggedIn: false };

  it("renders landing page content", () => {
    Auth.currentUserInfo.mockResolvedValue(null);
    const { container } = renderPage(Index, options);
    expect(container.firstChild).toMatchSnapshot();
  });

  it("shows employer information ", () => {
    Auth.currentUserInfo.mockResolvedValue(null);
    renderPage(Index, options);
    expect(
      screen.getByRole("heading", { name: "Employers" })
    ).toBeInTheDocument();
    expect(screen.getByText(/Manage leave for your team./)).toBeInTheDocument();
  });

  it("when user is logged in, redirects to applications", async () => {
    const goTo = jest.fn();
    Auth.currentUserInfo.mockResolvedValue({
      id: "us-east-1:XXXXXX",
      attributes: {
        email: "test@email.com",
      },
    });
    options.isLoggedIn = true;
    options.addCustomSetup = (appLogicHook) => {
      appLogicHook.portalFlow.goTo = goTo;
    };
    renderPage(Index, options);

    await waitFor(() => {
      expect(goTo).toHaveBeenCalledWith(
        "/applications",
        {},
        { redirect: true }
      );
    });
  });

  it("does not redirect to applications when user isn't logged in", async () => {
    const goTo = jest.fn();
    Auth.currentUserInfo.mockResolvedValue(null);
    options.addCustomSetup = (appLogicHook) => {
      appLogicHook.portalFlow.goTo = goTo;
    };
    renderPage(Index, options);

    await waitFor(() => {
      expect(goTo).not.toHaveBeenCalled();
    });
  });
});
