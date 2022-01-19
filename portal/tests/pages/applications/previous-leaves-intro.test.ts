import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import PreviousLeavesIntro from "../../../src/pages/applications/previous-leaves-intro";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const setup = () => {
  const claims = [new MockBenefitsApplicationBuilder().continuous().create()];
  const goToNextPageSpy = jest.fn(() => {
    return Promise.resolve();
  });

  const utils = renderPage(
    PreviousLeavesIntro,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, claims);
        appLogic.portalFlow.goToNextPage = goToNextPageSpy;
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );

  return { goToNextPageSpy, ...utils };
};

describe("PreviousLeavesIntro", () => {
  it("renders the page", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("calls goToNextPage when user submits form", async () => {
    const { goToNextPageSpy } = setup();

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(goToNextPageSpy).toHaveBeenCalledTimes(1);
    });
  });
});
