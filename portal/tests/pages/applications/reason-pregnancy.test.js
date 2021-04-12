import { renderWithAppLogic, simulateEvents } from "../../test-utils";
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
  it("renders the page", () => {
    const { wrapper } = setup({
      pregnant_or_recent_birth,
    });
    expect(wrapper).toMatchSnapshot();
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
        },
      }
    );
  });
});
