import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import Name from "../../../src/pages/applications/name";
import { pick } from "lodash";

jest.mock("../../../src/hooks/useAppLogic");

const defaultName = {
  first_name: "Aquib",
  middle_name: "cricketer",
  last_name: "Khan",
};
const setup = (name) => {
  const { appLogic, wrapper } = renderWithAppLogic(Name, {
    claimAttrs: {
      ...name,
    },
  });

  const { changeField, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeField,
    submitForm,
    wrapper,
  };
};

describe("Name", () => {
  it("renders the page", () => {
    const { wrapper } = setup(defaultName);
    expect(wrapper).toMatchSnapshot();
  });

  it("calls claims.update when the form is successfully submitted with pre-filled data", async () => {
    const { appLogic, submitForm } = setup(defaultName);

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      expect.any(String),
      pick(defaultName, ["first_name", "last_name", "middle_name"])
    );
  });

  it("calls claims.update when the form is successfully submitted with new data", async () => {
    const { appLogic, changeField, submitForm } = setup({});

    changeField("first_name", defaultName.first_name);
    changeField("middle_name", defaultName.middle_name);
    changeField("last_name", defaultName.last_name);

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      expect.any(String),
      pick(defaultName, ["first_name", "last_name", "middle_name"])
    );
  });
});
