import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import BenefitsApplicationCollection from "../../../src/models/BenefitsApplicationCollection";
import OtherIncomes from "../../../src/pages/applications/other-incomes";
import userEvent from "@testing-library/user-event";

jest.mock("../../../src/hooks/useAppLogic");

const otherIncomeClaim = new MockBenefitsApplicationBuilder()
  .continuous()
  .otherIncome()
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

  return renderPage(OtherIncomes, options, { query: { claim_id } });
};

describe("OtherIncomes", () => {
  it("renders the page", () => {
    const { container } = render();
    expect(container.firstChild).toMatchSnapshot();
  });

  it("calls claims.update with expected API fields when user selects Yes", async () => {
    render(otherIncomeClaim);

    userEvent.click(
      screen.getByRole("radio", {
        name: "Yes I will recieve other income from other sources during my paid leave",
      })
    );
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(update).toHaveBeenCalledWith(claim_id, {
        has_other_incomes: true,
      });
    });
  });

  it("calls claims.update with expected API fields when user selects No", async () => {
    render();

    userEvent.click(
      screen.getByRole("radio", {
        name: "No I won't receive other income from the above sources during my paid leave, I've applied but it hasn't been approved, or I don’t know the income amount yet",
      })
    );
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(update).toHaveBeenCalledWith(claim_id, {
        has_other_incomes: false,
      });
    });
  });

  it("calls claims.update with expected API fields when claim already has data", async () => {
    render(otherIncomeClaim);

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(update).toHaveBeenCalledWith(claim_id, {
        has_other_incomes: true,
      });
    });
  });

  it("deletes other income entries if user previously entered any and then selects No", async () => {
    render(otherIncomeClaim);

    userEvent.click(
      screen.getByRole("radio", {
        name: "No I won't receive other income from the above sources during my paid leave, I've applied but it hasn't been approved, or I don’t know the income amount yet",
      })
    );
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(update).toHaveBeenCalledWith(claim_id, {
        has_other_incomes: false,
        other_incomes: null,
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
        name: "Yes I will recieve other income from other sources during my paid leave",
      })
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();

    // conditional alert should render if the choice is "No"
    userEvent.click(
      screen.getByRole("radio", {
        name: "No I won't receive other income from the above sources during my paid leave, I've applied but it hasn't been approved, or I don’t know the income amount yet",
      })
    );
    const alert = screen.getByRole("alert");
    expect(alert).toMatchSnapshot();
  });
});
