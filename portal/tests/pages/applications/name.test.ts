import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import BenefitsApplicationCollection from "../../../src/models/BenefitsApplicationCollection";
import Name from "../../../src/pages/applications/name";
import { act } from "react-dom/test-utils";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

jest.mock("../../../src/hooks/useAppLogic");

describe("Name", () => {
  it("renders the page", () => {
    const { container } = renderPage(
      Name,
      {
        addCustomSetup: (appLogicHook) => {
          appLogicHook.benefitsApplications.benefitsApplications =
            new BenefitsApplicationCollection([
              new MockBenefitsApplicationBuilder().create(),
            ]);
        },
      },
      { query: { claim_id: "mock_application_id" }, claim: {} }
    );
    expect(container.firstChild).toMatchSnapshot();
  });

  it("enables user to fill and submit name information", async () => {
    const updateClaim = jest.fn(() => {
      return Promise.resolve();
    });
    renderPage(
      Name,
      {
        addCustomSetup: (appLogicHook) => {
          appLogicHook.benefitsApplications.update = updateClaim;
          appLogicHook.benefitsApplications.benefitsApplications =
            new BenefitsApplicationCollection([
              new MockBenefitsApplicationBuilder().create(),
            ]);
        },
      },
      { query: { claim_id: "mock_application_id" }, claim: {} }
    );

    const firstNameInput = screen.getByRole("textbox", { name: "First name" });
    const middleNameInput = screen.getByRole("textbox", {
      name: "Middle name (optional)",
    });
    const lastNameInput = screen.getByRole("textbox", { name: "Last name" });
    expect(firstNameInput).toHaveValue("");
    expect(middleNameInput).toHaveValue("");
    expect(lastNameInput).toHaveValue("");

    userEvent.type(firstNameInput, "Ali");
    userEvent.type(middleNameInput, "Grace Meadow");
    userEvent.type(lastNameInput, "Glenesk");
    expect(firstNameInput).toHaveValue("Ali");
    expect(middleNameInput).toHaveValue("Grace Meadow");
    expect(lastNameInput).toHaveValue("Glenesk");

    expect(updateClaim).not.toHaveBeenCalled();
    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });
    await act(async () => {
      await userEvent.click(submitButton);
    });
    expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
      first_name: "Ali",
      last_name: "Glenesk",
      middle_name: "Grace Meadow",
    });
  });
});
