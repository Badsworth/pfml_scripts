import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import FamilyMemberName from "../../../src/pages/applications/family-member-name";

const setup = () => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(FamilyMemberName);

  const { changeField, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeField,
    claim,
    submitForm,
    wrapper,
  };
};

describe("FamilyMemberName", () => {
  it("renders the page", () => {
    const { wrapper } = setup();

    expect(wrapper).toMatchSnapshot();
  });

  it("calls goToNextPage when user submits form", async () => {
    const { appLogic, wrapper } = setup();
    const spy = jest.spyOn(appLogic.portalFlow, "goToNextPage");

    const { submitForm } = simulateEvents(wrapper);
    await submitForm();
    expect(spy).toHaveBeenCalledTimes(1);
  });
});
