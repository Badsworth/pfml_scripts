import { mockAuth, mockFetch, renderPage } from "../test-utils";
import { screen, waitFor } from "@testing-library/react";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import React from "react";
import User from "../../src/models/User";
import { mockRouter } from "next/router";
import routes from "../../src/routes";
import withUser from "../../src/hoc/withUser";

jest.mock("../../src/services/tracker");

const mockPageContent = "User is logged in. This is the page";
const mockUser = new User({ user_id: "mock-user-id" });

function mockLoggedInUser(consented_to_data_sharing = true) {
  mockAuth();
  mockFetch({
    status: 200,
    response: { data: { ...mockUser, consented_to_data_sharing } },
  });
}

function setup({ addCustomSetup, pathname = routes.applications.index } = {}) {
  // Set the router path so we can assert against it in redirect tests
  mockRouter.asPath = pathname;
  mockRouter.pathname = pathname;

  const PageComponent = (props) => (
    <div>
      {mockPageContent} {props.user.user_id}
    </div>
  );
  const WrappedComponent = withUser(PageComponent);

  return renderPage(WrappedComponent, {
    addCustomSetup,
    // We don't use the authentication mocking behavior of renderPage
    // because it mocks some of the user/auth logic that this test file
    // depends on being unmocked
    isLoggedIn: false,
  });
}

describe("withUser", () => {
  it("shows spinner when loading authentication state", async () => {
    setup();

    expect(await screen.findByRole("progressbar")).toBeInTheDocument();
  });

  it("shows page when user is authenticated and consented to data sharing", async () => {
    mockLoggedInUser();
    setup();

    expect(
      await screen.findByText(mockPageContent, { exact: false })
    ).toBeInTheDocument();

    // Assert that withUser is passing in the user as a prop to our page component:
    expect(
      await screen.findByText(mockUser.user_id, { exact: false })
    ).toBeInTheDocument();
  });

  it("redirects unauthenticated users", async () => {
    let spy;
    const pathname = routes.applications.index;
    mockAuth(false);
    setup({
      addCustomSetup: (appLogic) => {
        spy = jest.spyOn(appLogic.portalFlow, "goTo");
      },
      pathname,
    });

    await waitFor(() => {
      expect(spy).toHaveBeenCalledWith("/login", {
        next: pathname,
      });
    });
  });

  it("redirects authenticated users who have not consented to data sharing", async () => {
    let spy;
    mockLoggedInUser(false);
    setup({
      addCustomSetup: (appLogic) => {
        spy = jest.spyOn(appLogic.portalFlow, "goTo");
      },
    });

    await waitFor(() => {
      expect(spy).toHaveBeenCalledWith(routes.user.consentToDataSharing);
    });
  });

  it("does not redirect authenticated users who have not consented to data sharing when on the consent page", async () => {
    mockLoggedInUser(false);
    setup({ pathname: routes.user.consentToDataSharing });

    expect(
      await screen.findByText(mockPageContent, { exact: false })
    ).toBeInTheDocument();
  });

  it("shows spinner for authenticated user if there's an error", async () => {
    mockLoggedInUser();
    setup({
      addCustomSetup: (appLogic) => {
        appLogic.appErrors = new AppErrorInfoCollection([new AppErrorInfo()]);
      },
    });

    expect(await screen.findByRole("progressbar")).toBeInTheDocument();
  });
});
