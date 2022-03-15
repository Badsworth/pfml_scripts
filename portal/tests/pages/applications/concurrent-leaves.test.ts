import {
  MockBenefitsApplicationBuilder,
  createMockBenefitsApplication,
  renderPage,
} from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";

import { AppLogic } from "../../../src/hooks/useAppLogic";
import ConcurrentLeaves from "../../../src/pages/applications/concurrent-leaves";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});

const setup = (...types: Array<keyof MockBenefitsApplicationBuilder>) => {
  const cb = (appLogic: AppLogic) => {
    appLogic.benefitsApplications.update = updateClaim;
  };

  return renderPage(
    ConcurrentLeaves,
    {
      addCustomSetup: (hook) => {
        setupBenefitsApplications(
          hook,
          [createMockBenefitsApplication(...types)],
          cb
        );
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("ConcurrentLeaves", () => {
  it("renders the page", () => {
    const { container } = setup("continuous", "concurrentLeave", "employed");
    expect(container).toMatchSnapshot();
  });

  it("renders the continuous page content", () => {
    const { container } = setup("continuous");
    expect(container).toMatchSnapshot();
  });

  it("renders the reduced page content", () => {
    const { container } = setup("reducedSchedule");
    expect(container).toMatchSnapshot();
  });

  it("renders the intermittent reduced page content", () => {
    const { container } = setup("intermittent");
    expect(container).toMatchSnapshot();
  });

  it("calls claims.update when user clicks continue", async () => {
    setup("continuous", "concurrentLeave", "employed");

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        has_concurrent_leave: true,
      });
    });
  });

  it("sends concurrent_leave as null to the API if has_concurrent_leave changes to no", async () => {
    setup("continuous", "concurrentLeave", "employed");

    userEvent.click(
      screen.getByRole("radio", { name: /No I don’t need to report/i })
    );
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        has_concurrent_leave: false,
        concurrent_leave: null,
      });
    });
  });

  it("renders the page when the claim does not contain concurrent leave data", () => {
    const { container } = setup("continuous", "employed");
    expect(container).toMatchSnapshot();
  });

  it("with no concurrent leave data, user can click no and expected info is sent to API", async () => {
    setup("continuous", "employed");

    userEvent.click(
      screen.getByRole("radio", { name: /No I don’t need to report/i })
    );

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        has_concurrent_leave: false,
      });
    });
  });

  it("with no concurrent leave data, user can click yes and expected info is sent to API", async () => {
    setup("continuous", "employed");

    userEvent.click(
      screen.getByRole("radio", { name: /yes i need to report/i })
    );

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        has_concurrent_leave: true,
      });
    });
  });
});
