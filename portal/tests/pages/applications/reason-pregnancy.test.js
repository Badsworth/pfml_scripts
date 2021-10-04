import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import LeaveReason from "../../../src/models/LeaveReason";
import ReasonPregnancy from "../../../src/pages/applications/reason-pregnancy";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const setup = ({ claim } = {}) => {
  claim = claim ?? new MockBenefitsApplicationBuilder().create();
  const updateSpy = jest.fn(() => Promise.resolve());

  const utils = renderPage(
    ReasonPregnancy,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        appLogic.benefitsApplications.update = updateSpy;
      },
    },
    { query: { claim_id: claim.application_id } }
  );

  return { updateSpy, ...utils };
};

describe("ReasonPregnancy", () => {
  it("renders the page with no answer", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("submits expected data when the user doesn't select a response and clicks save and continue", async () => {
    const { updateSpy } = setup();

    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => expect(updateSpy).toHaveBeenCalled());

    expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
      leave_details: {
        pregnant_or_recent_birth: null,
      },
    });
  });

  it("submits expected data when the user selects a response and clicks save and continue", async () => {
    const { updateSpy } = setup();

    userEvent.click(screen.getByRole("radio", { name: /yes/i }));
    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => expect(updateSpy).toHaveBeenCalled());

    expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
      leave_details: {
        pregnant_or_recent_birth: true,
        reason: LeaveReason.pregnancy,
      },
    });
  });

  it("submits existing data when the user doesn't change their answer and clicks save", async () => {
    const { updateSpy } = setup({
      claim: new MockBenefitsApplicationBuilder()
        .pregnancyLeaveReason()
        .create(),
    });

    userEvent.click(screen.getByRole("button", { name: /save/i }));
    await waitFor(() => expect(updateSpy).toHaveBeenCalled());

    expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
      leave_details: {
        pregnant_or_recent_birth: true,
        reason: LeaveReason.pregnancy,
      },
    });
  });

  it("updates leave reason to pregnancy when the user answers yes", async () => {
    const { updateSpy } = setup({
      claim: new MockBenefitsApplicationBuilder().medicalLeaveReason().create(),
    });

    userEvent.click(screen.getByRole("radio", { name: /yes/i }));
    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => expect(updateSpy).toHaveBeenCalled());
    expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
      leave_details: {
        pregnant_or_recent_birth: true,
        reason: LeaveReason.pregnancy,
      },
    });
  });

  it("updates leave reason to medical when the user answers no and leave reason is pregnancy", async () => {
    const { updateSpy } = setup({
      claim: new MockBenefitsApplicationBuilder()
        .pregnancyLeaveReason()
        .create(),
    });

    userEvent.click(screen.getByRole("radio", { name: /no/i }));
    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => expect(updateSpy).toHaveBeenCalled());
    expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
      leave_details: {
        pregnant_or_recent_birth: false,
        reason: LeaveReason.medical,
      },
    });
  });
});
