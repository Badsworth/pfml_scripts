import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import ConcurrentLeaves from "../../../src/pages/applications/concurrent-leaves";
import { mount } from "enzyme";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (options = { hasConcurrentLeave: true }) => {
  const claim = options.hasConcurrentLeave
    ? new MockBenefitsApplicationBuilder()
        .continuous()
        .concurrentLeave()
        .employed()
        .create()
    : new MockBenefitsApplicationBuilder().continuous().employed().create();

  const { appLogic, wrapper } = renderWithAppLogic(ConcurrentLeaves, {
    claimAttrs: claim,
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

describe("ConcurrentLeaves", () => {
  it("renders the page", () => {
    const { wrapper } = setup();
    const inputChoiceGroupHint = wrapper.find("InputChoiceGroup").prop("hint");
    const hintComponent = mount(inputChoiceGroupHint);

    expect(wrapper).toMatchSnapshot();
    expect(hintComponent).toMatchSnapshot();
  });

  it("calls claims.update when user clicks continue", async () => {
    const { appLogic, claim, submitForm } = setup();

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        has_concurrent_leave: claim.has_concurrent_leave,
      }
    );
  });

  it("sends concurrent_leave as null to the API if has_concurrent_leave changes to no", async () => {
    const { appLogic, changeRadioGroup, claim, submitForm } = setup();

    changeRadioGroup("has_concurrent_leave", "false");

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        has_concurrent_leave: false,
        concurrent_leave: null,
      }
    );
  });
});

describe("when the claim does not contain concurrent leave data", () => {
  const disableConcurrentLeave = { hasConcurrentLeave: false };

  it("renders the page", () => {
    const { wrapper } = setup(disableConcurrentLeave);
    expect(wrapper).toMatchSnapshot();
  });

  it("sends the user's input to the API when the user clicks continue", async () => {
    const { appLogic, changeRadioGroup, claim, submitForm } = setup(
      disableConcurrentLeave
    );

    // check that "false" works
    changeRadioGroup("has_concurrent_leave", false);

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        has_concurrent_leave: false,
      }
    );

    // check that "true" works
    changeRadioGroup("has_concurrent_leave", true);

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        has_concurrent_leave: true,
      }
    );
  });
});
