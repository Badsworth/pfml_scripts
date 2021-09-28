import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import ConcurrentLeaves from "../../../src/pages/applications/concurrent-leaves";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});

const setup = (options = { hasConcurrentLeave: true }) => {
  const claim = options.hasConcurrentLeave
    ? new MockBenefitsApplicationBuilder()
        .continuous()
        .concurrentLeave()
        .employed()
        .create()
    : new MockBenefitsApplicationBuilder().continuous().employed().create();

  const claims = [claim];
  const cb = (appLogic) => {
    appLogic.benefitsApplications.update = updateClaim;
  };
  return renderPage(
    ConcurrentLeaves,
    {
      addCustomSetup: (hook) => {
        setupBenefitsApplications(hook, claims, cb);
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("ConcurrentLeaves", () => {
  it("renders the page", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("calls claims.update when user clicks continue", async () => {
    setup();

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        has_concurrent_leave: true,
      });
    });
  });

  it("sends concurrent_leave as null to the API if has_concurrent_leave changes to no", async () => {
    setup();

    userEvent.click(screen.getByRole("radio", { name: "No" }));
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        has_concurrent_leave: false,
        concurrent_leave: null,
      });
    });
  });

  it("renders the page when the claim does not contain concurrent leave data", () => {
    const { container } = setup({ hasConcurrentLeave: false });
    expect(container).toMatchSnapshot();
  });

  it("with no concurrent leave data, user can click no and expected info is sent to API", async () => {
    setup({ hasConcurrentLeave: false });

    userEvent.click(screen.getByRole("radio", { name: "No" }));

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        has_concurrent_leave: false,
      });
    });
  });

  it("with no concurrent leave data, user can click yes and expected info is sent to API", async () => {
    setup({ hasConcurrentLeave: false });

    userEvent.click(screen.getByRole("radio", { name: "Yes" }));

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        has_concurrent_leave: true,
      });
    });
  });
});
