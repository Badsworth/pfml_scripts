import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import ConcurrentLeavesIntro from "../../../src/pages/applications/concurrent-leaves-intro";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const goToNextPage = jest.fn(() => {
  return Promise.resolve();
});

const setup = () => {
  const claims = [new MockBenefitsApplicationBuilder().continuous().create()];
  const cb = (appLogic) => {
    appLogic.portalFlow.goToNextPage = goToNextPage;
  };
  return renderPage(
    ConcurrentLeavesIntro,
    {
      addCustomSetup: (hook) => {
        setupBenefitsApplications(hook, claims, cb);
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("ConcurrentLeavesIntroIntro", () => {
  it("renders the page", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("calls goToNextPage when user submits form", async () => {
    setup();

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(goToNextPage).toHaveBeenCalledTimes(1);
    });
  });
});
