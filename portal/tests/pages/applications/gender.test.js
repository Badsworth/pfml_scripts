import { renderWithAppLogic, simulateEvents } from "../../test-utils";

import Gender from "../../../src/pages/applications/gender";
import { pick } from "lodash";

jest.mock("../../../src/hooks/useAppLogic");

const defaultGender = {
  gender: "Woman", //
};
const setup = (gender) => {
  const { appLogic, wrapper } = renderWithAppLogic(Gender, {
    claimAttrs: {
      ...gender,
    },
  });

  const { changeRadioGroup, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeRadioGroup,
    submitForm,
    wrapper,
  };
};

describe("Gender", () => {
  it("renders the page", () => {
    const { wrapper } = setup(defaultGender);
    expect(wrapper).toMatchSnapshot();
  });

  it("calls claims.update when the form is successfully submitted with pre-filled data", async () => {
    const { appLogic, submitForm } = setup(defaultGender);

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      expect.any(String),
      pick(defaultGender, ["gender"])
    );
  });

  it("calls claims.update when the form is successfully submitted with new data", async () => {
    const { appLogic, changeRadioGroup, submitForm } = setup({});

    changeRadioGroup("gender", defaultGender.gender);

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      expect.any(String),
      pick(defaultGender, ["gender"])
    );
  });
});
