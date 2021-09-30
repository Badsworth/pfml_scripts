import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import BenefitsApplicationCollection from "../../../src/models/BenefitsApplicationCollection";
import EmployerBenefits from "../../../src/pages/applications/employer-benefits";
import userEvent from "@testing-library/user-event";

jest.mock("../../../src/hooks/useAppLogic");

const employerBenefitClaim = new MockBenefitsApplicationBuilder()
  .continuous()
  .employerBenefit()
  .employed()
  .create();

const update = jest.fn(() => {
  return Promise.resolve();
});
const claim_id = "mock_application_id";

const render = (
  claimAttrs = new MockBenefitsApplicationBuilder().continuous().create()
) => {
  const options = {
    addCustomSetup: (appLogic) => {
      appLogic.benefitsApplications.update = update;
      appLogic.benefitsApplications.benefitsApplications =
        new BenefitsApplicationCollection([claimAttrs]);
    },
    isLoggedIn: true,
  };

  return renderPage(EmployerBenefits, options, { query: { claim_id } });
};

describe("EmployerBenefits", () => {
  it("renders the page", () => {
    const { container } = render();
    expect(container.firstChild).toMatchSnapshot();
  });

  it("calls claims.update with expected API fields when user selects Yes", async () => {
    render(employerBenefitClaim);

    userEvent.click(
      screen.getByRole("radio", {
        name: "Yes I will recieve employer sponsored benefits during my paid leave",
      })
    );
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(update).toHaveBeenCalledWith(claim_id, {
        has_employer_benefits: true,
      });
    });
  });

  it("calls claims.update with expected API fields when user selects No", async () => {
    render();

    userEvent.click(
      screen.getByRole("radio", {
        name: "No I won’t receive employer-sponsored benefits, I've applied but it hasn't been approved, or I don’t know the benefit amount yet",
      })
    );
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(update).toHaveBeenCalledWith(claim_id, {
        has_employer_benefits: false,
      });
    });
  });

  it("calls claims.update with expected API fields when claim already has data", async () => {
    render(employerBenefitClaim);

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(update).toHaveBeenCalledWith(claim_id, {
        has_employer_benefits: true,
      });
    });
  });

  it("deletes employer benefit entries if user previously entered any and then selects No", async () => {
    render(employerBenefitClaim);

    userEvent.click(
      screen.getByRole("radio", {
        name: "No I won’t receive employer-sponsored benefits, I've applied but it hasn't been approved, or I don’t know the benefit amount yet",
      })
    );
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(update).toHaveBeenCalledWith(claim_id, {
        has_employer_benefits: false,
        employer_benefits: null,
      });
    });
  });

  it("conditionally renders an info alert when user selects No", () => {
    render();

    // conditional alert should not render if no choice is made
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();

    // conditional alert should not render if the choice is "Yes"
    userEvent.click(
      screen.getByRole("radio", {
        name: "Yes I will recieve employer sponsored benefits during my paid leave",
      })
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();

    // conditional alert should render if the choice is "No"
    userEvent.click(
      screen.getByRole("radio", {
        name: "No I won’t receive employer-sponsored benefits, I've applied but it hasn't been approved, or I don’t know the benefit amount yet",
      })
    );
    const alert = screen.getByRole("alert");
    expect(alert).toMatchSnapshot();
  });
});
