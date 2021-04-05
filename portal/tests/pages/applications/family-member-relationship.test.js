import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import FamilyMemberRelationship from "../../../src/pages/applications/family-member-relationship";

const setup = () => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(
    FamilyMemberRelationship
  );

  const { changeRadioGroup, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeRadioGroup,
    claim,
    submitForm,
    wrapper,
  };
};

describe("FamilyMemberRelationship", () => {
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
