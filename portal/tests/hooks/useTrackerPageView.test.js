import { act, renderHook } from "@testing-library/react-hooks";
import { mockRouterEvents } from "next/router";
import tracker from "../../src/services/tracker";
import useTrackerPageView from "../../src/hooks/useTrackerPageView";

jest.mock("../../src/services/tracker");

describe("New Relic page view tracking", () => {
  const user = null;

  const triggerRouterEvent = async (eventName, url = "/", options = {}) => {
    const routeChangeStart = mockRouterEvents.find(
      (evt) => evt.name === eventName
    );

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
      routeChangeStart.callback(url, options);
    });
  };

  it("tracks page view on load", () => {
    renderHook(() => useTrackerPageView(user));
    expect(tracker.startPageView).toHaveBeenCalledTimes(1);
  });

  it("tracks page view on when route changes", async () => {
    renderHook(() => useTrackerPageView(user));
    expect(tracker.startPageView).toHaveBeenCalledTimes(1);

    await triggerRouterEvent("routeChangeComplete", "/login");

    expect(tracker.startPageView).toHaveBeenCalledTimes(2);
  });

  it("does not track page view when redirected to /applications as an employer", async () => {
    const updatedUser = {
      auth_id: "000",
      hasEmployerRole: true,
    };

    renderHook(() => useTrackerPageView(updatedUser));
    expect(tracker.startPageView).toHaveBeenCalledTimes(1);

    await triggerRouterEvent("routeChangeComplete", "/applications/");
    expect(tracker.startPageView).toHaveBeenCalledTimes(1);
  });

  it("does track page view and attributes when on /applications/claim as a claimaint", async () => {
    const updatedUser = {
      auth_id: "000",
      hasEmployerRole: false,
    };
    renderHook(() => useTrackerPageView(updatedUser));

    // values get reassigned before sending to new relic. This is to make sure it matches up
    // with what actually gets called when we start a page view
    const pageAttributes = {
      "user.auth_id": updatedUser.auth_id,
      "user.has_employer_role": updatedUser.hasEmployerRole,
      "user.is_logged_in": true,
      query_claim_id: "12345",
    };

    await triggerRouterEvent(
      "routeChangeComplete",
      "/applications/checklist/?claim_id=12345"
    );
    expect(tracker.startPageView).toHaveBeenCalledTimes(2);
    expect(tracker.startPageView).toHaveBeenCalledWith(
      "/applications/checklist/",
      pageAttributes
    );
  });

  it("tracks page view with proper attributes", () => {
    const updatedUser = { auth_id: "000", hasEmployerRole: false };

    // values get reassigned before sending to new relic. This is to make sure it matches up
    // with what actually gets called when we start a page view
    const pageAttributes = {
      "user.auth_id": updatedUser.auth_id,
      "user.has_employer_role": updatedUser.hasEmployerRole,
      "user.is_logged_in": true,
    };

    renderHook(() => useTrackerPageView(updatedUser));
    expect(tracker.startPageView).toHaveBeenCalledTimes(1);
    expect(tracker.startPageView).toHaveBeenCalledWith("/", pageAttributes);
  });
});
