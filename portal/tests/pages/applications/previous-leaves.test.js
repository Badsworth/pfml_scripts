import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import PreviousLeaves from "../../../src/pages/applications/previous-leaves";
import { shallow } from "enzyme";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claim) => {
  if (!claim) {
    claim = new MockClaimBuilder().continuous().create();
  }

  const { appLogic, wrapper } = renderWithAppLogic(PreviousLeaves, {
    claimAttrs: claim,
  });

  const { changeRadioGroup, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    claim,
    changeRadioGroup,
    submitForm,
    wrapper,
  };
};

describe("PreviousLeaves", () => {
  it("renders the page", () => {
    const { wrapper } = setup();

    const hintWrapper = shallow(wrapper.find("InputChoiceGroup").prop("hint"));

    expect(wrapper).toMatchSnapshot();
    expect(hintWrapper.find("Trans").dive()).toMatchSnapshot();
  });

  it("calls claims.update when user clicks continue", async () => {
    const { appLogic, claim, wrapper } = setup();
    const { submitForm } = simulateEvents(wrapper);

    await submitForm();

    expect(appLogic.claims.update).toHaveBeenCalledWith(claim.application_id, {
      has_previous_leaves: claim.has_previous_leaves,
    });
  });

  it("sends previous_leaves as null to the API if has_previous_leaves changes to no", async () => {
    const claim = new MockClaimBuilder()
      .previousLeavePregnancyFromOtherEmployer()
      .create();

    const { appLogic, changeRadioGroup, submitForm } = setup(claim);

    changeRadioGroup("has_previous_leaves", "false");

    await submitForm();

    expect(appLogic.claims.update).toHaveBeenCalledWith(claim.application_id, {
      has_previous_leaves: false,
      previous_leaves: null,
    });
  });
});
