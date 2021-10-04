import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import PhoneNumber from "../../../src/pages/applications/phone-number";
import { PhoneType } from "../../../src/models/BenefitsApplication";

jest.mock("../../../src/hooks/useAppLogic");

const phone_number = "123-456-7890";
const phone_type = PhoneType.cell;

const setup = (phone = {}) => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(PhoneNumber, {
    claimAttrs: {
      phone,
    },
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

describe("PhoneNumber", () => {
  it("renders the page", () => {
    const { wrapper } = setup({ phone_number, phone_type });
    expect(wrapper).toMatchSnapshot();
  });

  it("calls claims.update when the form is successfully submitted with existing data", () => {
    const { appLogic, claim, submitForm } = setup({ phone_number, phone_type });

    submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        phone: {
          int_code: "1",
          phone_number,
          phone_type,
        },
      }
    );
  });

  it("calls claims.update when the form is successfully submitted with newly entered data", () => {
    const { appLogic, changeField, changeRadioGroup, claim, submitForm } =
      setup();

    changeRadioGroup("phone.phone_type", phone_type);
    changeField("phone.phone_number", phone_number);

    submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        phone: {
          int_code: "1",
          phone_number,
          phone_type,
        },
      }
    );
  });
});
