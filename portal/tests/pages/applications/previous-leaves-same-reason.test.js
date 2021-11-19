import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { cleanup, screen, waitFor } from "@testing-library/react";
import PreviousLeavesSameReason from "../../../src/pages/applications/previous-leaves-same-reason";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const setup = (
  claim = new MockBenefitsApplicationBuilder().continuous().create()
) => {
  let updateSpy;

  const utils = renderPage(
    PreviousLeavesSameReason,
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

describe("PreviousLeavesSameReason", () => {
  it("renders different legend and hint when claim is for Caring Leave", () => {
    setup(
      new MockBenefitsApplicationBuilder()
        .continuous()
        .caringLeaveReason()
        .create()
    );

    expect(screen.getByRole("group")).toMatchSnapshot();

    cleanup();
    setup(
      new MockBenefitsApplicationBuilder()
        .continuous()
        .medicalLeaveReason()
        .create()
    );

    expect(screen.getByRole("group")).toMatchSnapshot();
  });

  it("submits form with has_previous_leaves_same_reason value", async () => {
    const { updateSpy } = setup();

    userEvent.click(screen.getByRole("radio", { name: /Yes/i }));
    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
        has_previous_leaves_same_reason: true,
      });
    });
  });

  it("sets previous_leaves_same_reason to null when has_previous_leaves_same_reason changes to false", async () => {
    const { updateSpy } = setup(
      new MockBenefitsApplicationBuilder().previousLeavesSameReason().create()
    );

    userEvent.click(screen.getByRole("radio", { name: /No/i }));
    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
        has_previous_leaves_same_reason: false,
        previous_leaves_same_reason: null,
      });
    });
  });
});
