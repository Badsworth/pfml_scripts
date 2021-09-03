import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import LeaveReason from "../../../src/models/LeaveReason";
import ReasonPregnancy from "../../../src/pages/applications/reason-pregnancy";

jest.mock("../../../src/hooks/useAppLogic");

const pregnant_or_recent_birth = false;

const setup = (leave_details = {}) => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(ReasonPregnancy, {
    claimAttrs: {
      leave_details,
    },
  });

  const { changeRadioGroup, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeRadioGroup,
    claim,
    submitForm,
    wrapper,
  };
};

describe("ReasonPregnancy", () => {
  it("renders the page with no answer", () => {
    const { wrapper } = setup();
    expect(wrapper).toMatchSnapshot();
  });

  it("calls claims.update when the user doesn't select a response and clicks save and continue", async () => {
    const { appLogic, claim, submitForm } = setup();

    await submitForm();
    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        leave_details: {
          pregnant_or_recent_birth: null,
        },
      }
    );
  });

  it("calls claims.update when the user selects a response and clicks save and continue", async () => {
    const { appLogic, changeRadioGroup, claim, submitForm } = setup();

    changeRadioGroup(
      "leave_details.pregnant_or_recent_birth",
      pregnant_or_recent_birth
    );

    await submitForm();
    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        leave_details: {
          pregnant_or_recent_birth,
          reason: LeaveReason.medical,
        },
      }
    );
  });

  it("calls claims.update with existing data when the user clicks save and continue", async () => {
    const { appLogic, claim, submitForm } = setup({
      pregnant_or_recent_birth,
    });

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        leave_details: {
          pregnant_or_recent_birth,
          reason: LeaveReason.medical,
        },
      }
    );
  });

  it("updates leave reason to pregnancy when the user answers yes", async () => {
    const { appLogic, changeRadioGroup, claim, submitForm } = setup({
      reason: LeaveReason.medical,
    });

    changeRadioGroup("leave_details.pregnant_or_recent_birth", true);

    await submitForm();
    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        leave_details: {
          pregnant_or_recent_birth: true,
          reason: LeaveReason.pregnancy,
        },
      }
    );
  });

  it("updates leave reason to medical when the user answers no and leave reason is pregnancy", async () => {
    const { appLogic, changeRadioGroup, claim, submitForm } = setup({
      reason: LeaveReason.pregnancy,
      pregnant_or_recent_birth: true,
    });

    changeRadioGroup("leave_details.pregnant_or_recent_birth", false);

    await submitForm();
    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        leave_details: {
          pregnant_or_recent_birth: false,
          reason: LeaveReason.medical,
        },
      }
    );
  });
});
