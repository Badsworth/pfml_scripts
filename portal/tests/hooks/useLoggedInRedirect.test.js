import { Auth } from "@aws-amplify/auth";
import { renderHook } from "@testing-library/react-hooks";
import useLoggedInRedirect from "../../src/hooks/useLoggedInRedirect";

jest.mock("@aws-amplify/auth");

function mockAuthenticatedUser() {
  Auth.currentUserInfo.mockResolvedValueOnce({});
}

function mockUnauthenticatedUser() {
  Auth.currentUserInfo.mockRejectedValueOnce();
}

function mockPortalFlow() {
  return {
    goTo: jest.fn(),
  };
}

/**
 * Since the logic we have in useEffect is async, we can't simply setup the hook and
 * call an assertion on it. We instead need to wait for the effect's promise to resolve
 * or reject before we can make assertions.
 * @returns {Promise<void>}
 */
function waitForUseEffectToComplete() {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

describe("useLoggedInRedirect", () => {
  it("redirects authenticated users to landing page by default", async () => {
    mockAuthenticatedUser();
    const portalFlow = mockPortalFlow();

    renderHook(() => {
      useLoggedInRedirect(portalFlow);
    });
    await waitForUseEffectToComplete();

    expect(portalFlow.goTo).toHaveBeenCalledWith("/", {}, { redirect: true });
  });

  it("redirects authenticated users to redirectTo param", async () => {
    mockAuthenticatedUser();
    const portalFlow = mockPortalFlow();

    renderHook(() => {
      useLoggedInRedirect(portalFlow, "/redirect-here");
    });
    await waitForUseEffectToComplete();

    expect(portalFlow.goTo).toHaveBeenCalledWith(
      "/redirect-here",
      {},
      { redirect: true }
    );
  });

  it("does not redirect unauthenticated users", async () => {
    mockUnauthenticatedUser();
    const portalFlow = mockPortalFlow();

    renderHook(() => {
      useLoggedInRedirect(portalFlow);
    });
    await waitForUseEffectToComplete();

    expect(portalFlow.goTo).not.toHaveBeenCalled();
  });
});
