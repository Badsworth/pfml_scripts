import { mockAuth, renderPage } from "../test-utils";
import { screen, waitFor } from "@testing-library/react";
import Index from "../../src/pages/index";

jest.mock("../../src/hooks/useAppLogic");

describe("Index", () => {
  const options: Parameters<typeof renderPage>[1] = { isLoggedIn: false };

  it("renders landing page content", () => {
    mockAuth(false);
    const { container } = renderPage(Index, options);
    expect(container.firstChild).toMatchSnapshot();
  });

  it("shows employer information ", () => {
    mockAuth(false);
    renderPage(Index, options);
    expect(
      screen.getByRole("heading", { name: "Employers" })
    ).toBeInTheDocument();
    expect(screen.getByText(/Manage leave for your team./)).toBeInTheDocument();
  });

  it("when user is logged in, redirects to applications", async () => {
    mockAuth();
    const goTo = jest.fn();

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
    mockAuth(false);
    options.addCustomSetup = (appLogicHook) => {
      appLogicHook.portalFlow.goTo = goTo;
    };
    renderPage(Index, options);

    await waitFor(() => {
      expect(goTo).not.toHaveBeenCalled();
    });
  });
});
