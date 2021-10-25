import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import PreviousLeavesOtherReason from "../../../src/pages/applications/previous-leaves-other-reason";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const setup = (
  claim = new MockBenefitsApplicationBuilder().continuous().create()
) => {
  let updateSpy;

  const utils = renderPage(
    PreviousLeavesOtherReason,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        updateSpy = jest.spyOn(appLogic.benefitsApplications, "update");
      },
    },
    { query: { claim_id: claim.application_id } }
  );

  return {
    updateSpy,
    ...utils,
  };
};

describe("PreviousLeavesOtherReason", () => {
  it("renders the page", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("submits form with has_previous_leaves_other_reason value", async () => {
    const { updateSpy } = setup();

    userEvent.click(screen.getByRole("radio", { name: /Yes/i }));
    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
        has_previous_leaves_other_reason: true,
      });
    });
  });

  it("sets previous_leaves_other_reason to null when has_previous_leaves_other_reason changes to false", async () => {
    const { updateSpy } = setup(
      new MockBenefitsApplicationBuilder().previousLeavesOtherReason().create()
    );

    userEvent.click(screen.getByRole("radio", { name: /No/i }));
    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
        has_previous_leaves_other_reason: false,
        previous_leaves_other_reason: null,
      });
    });
  });
});
