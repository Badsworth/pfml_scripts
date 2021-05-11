import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import PreviousLeave from "../../../src/models/PreviousLeave";
import PreviousLeavesSameReason from "../../../src/pages/applications/previous-leaves-same-reason";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs = {}) => {
  const {
    appLogic,
    claim,
    wrapper,
  } = renderWithAppLogic(PreviousLeavesSameReason, { claimAttrs });

  const { changeRadioGroup, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeRadioGroup,
    claim,
    submitForm,
    wrapper,
  };
};

describe("PreviousLeavesSameReason", () => {
  it("renders the page", () => {
    const { wrapper } = setup();

    expect(wrapper).toMatchSnapshot();
  });

  it("submits form with has_previous_leaves_same_reason value", async () => {
    const { appLogic, changeRadioGroup, claim, submitForm } = setup();
    const spy = jest.spyOn(appLogic.benefitsApplications, "update");

    await changeRadioGroup("has_previous_leaves_same_reason", "true");
    await submitForm();
    expect(spy).toHaveBeenCalledWith(claim.application_id, {
      has_previous_leaves_same_reason: true,
    });
  });

  it("sets previous_leaves_same_reason to null when has_previous_leaves_same_reason is false and previous_leaves exist", async () => {
    const { appLogic, changeRadioGroup, claim, submitForm } = setup({
      previous_leaves_same_reason: [new PreviousLeave()],
    });
    const spy = jest.spyOn(appLogic.benefitsApplications, "update");

    await changeRadioGroup("has_previous_leaves_same_reason", "false");
    await submitForm();
    expect(spy).toHaveBeenCalledWith(claim.application_id, {
      has_previous_leaves_same_reason: false,
      previous_leaves_same_reason: null,
    });
  });

  it("does not set previous_leaves_same_reason to null when has_previous_leaves_same_reason is false but previous_leaves do not exist", async () => {
    const { appLogic, changeRadioGroup, claim, submitForm } = setup({
      previous_leaves_same_reason: [],
    });
    const spy = jest.spyOn(appLogic.benefitsApplications, "update");

    await changeRadioGroup("has_previous_leaves_same_reason", "false");
    await submitForm();
    expect(spy).toHaveBeenCalledWith(claim.application_id, {
      has_previous_leaves_same_reason: false,
    });
  });
});
