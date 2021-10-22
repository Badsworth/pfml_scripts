import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import StateId from "../../../src/pages/applications/state-id";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const setup = () => {
  const claim = new MockBenefitsApplicationBuilder().create();
  const updateSpy = jest.fn(() => {
    return Promise.resolve();
  });
  const utils = renderPage(
    StateId,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        appLogic.benefitsApplications.update = updateSpy;
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
  return { updateSpy, ...utils };
};

describe("StateId", () => {
  it("initially renders the page with the ID text field hidden", () => {
    const { container } = setup();
    expect(container.firstChild).toMatchSnapshot();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });

  it("renders ID text field only when user indicates they have a state id", () => {
    setup();

    // I have a state ID
    userEvent.click(screen.getByRole("radio", { name: "Yes" }));
    expect(screen.queryByRole("textbox")).toBeInTheDocument();

    // I don't have a state ID
    userEvent.click(screen.getByRole("radio", { name: "No" }));
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });

  it("calls claims.update when the form is submitted", async () => {
    const mass_id = "SA3456789";
    const { updateSpy } = setup();

    userEvent.click(screen.getByRole("radio", { name: "No" }));
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith("mock_application_id", {
        has_state_id: false,
        mass_id: null,
      });
    });

    userEvent.click(screen.getByRole("radio", { name: "Yes" }));
    userEvent.type(screen.getByRole("textbox"), mass_id);
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith("mock_application_id", {
        has_state_id: true,
        mass_id,
      });
    });
  });
});
