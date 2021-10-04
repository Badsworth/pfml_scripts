import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import StateId from "../../../src/pages/applications/state-id";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs = {}) => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(StateId, {
    claimAttrs,
  });

  const { changeField, changeRadioGroup, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeField,
    changeRadioGroup,
    claim,
    submitForm,
    wrapper,
  };
};

const isStateIdTextFieldVisible = (wrapper) => {
  return wrapper.find("ConditionalContent").prop("visible");
};

describe("StateId", () => {
  it("initially renders the page with the ID text field hidden", () => {
    const { wrapper } = setup();

    expect(wrapper).toMatchSnapshot();
    expect(isStateIdTextFieldVisible(wrapper)).toBeFalsy();
  });

  it("renders ID text field only when user indicates they have a state id", () => {
    const { changeRadioGroup, wrapper } = setup();

    // I have a state ID
    changeRadioGroup("has_state_id", "true");
    expect(isStateIdTextFieldVisible(wrapper)).toBe(true);

    // I don't have a state ID
    changeRadioGroup("has_state_id", "false");
    expect(isStateIdTextFieldVisible(wrapper)).toBe(false);
  });

  it("calls claims.update when the form is submitted", async () => {
    const mass_id = "sa3456789";
    const { appLogic, changeField, changeRadioGroup, claim, submitForm } =
      setup({ has_state_id: false });

    // Existing data
    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        has_state_id: false,
        mass_id: null,
      }
    );

    // Changed answer to Yes
    changeRadioGroup("has_state_id", "true");
    changeField("mass_id", mass_id.toLowerCase());
    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        has_state_id: true,
        mass_id: mass_id.toUpperCase(),
      }
    );
  });
});
