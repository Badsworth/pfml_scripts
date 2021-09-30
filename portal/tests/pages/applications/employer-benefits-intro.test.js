import { screen, waitFor } from "@testing-library/react";
import EmployerBenefitsIntroIntro from "../../../src/pages/applications/employer-benefits-intro";
import { renderPage } from "../../test-utils";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const goToNextPage = jest.fn(() => {
  return Promise.resolve();
});

const setup = () => {
  return renderPage(
    EmployerBenefitsIntroIntro,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic);
        appLogic.portalFlow.goToNextPage = goToNextPage;
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("EmployerBenefitsIntroIntro", () => {
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
