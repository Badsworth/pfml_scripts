import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import ConcurrentLeavesDetails from "../../../src/pages/applications/concurrent-leaves-details";

jest.mock("../../../src/hooks/useAppLogic");

const setup = () => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(
    ConcurrentLeavesDetails,
    {
      claimAttrs: new MockBenefitsApplicationBuilder()
        .employed()
        .continuous()
        .create(),
    }
  );

  const { changeField, changeRadioGroup, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeRadioGroup,
    changeField,
    claim,
    submitForm,
    wrapper,
  };
};

const concurrentLeaveData = {
  is_for_current_employer: true,
  leave_start_date: "2021-05-01",
  leave_end_date: "2021-06-01",
};

describe("ConcurrentLeavesDetails", () => {
  it("renders the page", () => {
    const { wrapper } = setup();

    expect(wrapper).toMatchSnapshot();
  });

  it("calls claims.update with new concurrent leave data when user clicks continue", async () => {
    const {
      appLogic,
      changeField,
      changeRadioGroup,
      claim,
      submitForm,
    } = setup();

    changeRadioGroup(
      "concurrent_leave.is_for_current_employer",
      concurrentLeaveData.is_for_current_employer
    );
    changeField(
      "concurrent_leave.leave_start_date",
      concurrentLeaveData.leave_start_date
    );
    changeField(
      "concurrent_leave.leave_end_date",
      concurrentLeaveData.leave_end_date
    );

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        concurrent_leave: concurrentLeaveData,
      }
    );
  });

  it("calls claims.update with empty concurrent leave data when user does not enter data", async () => {
    const { appLogic, claim, submitForm } = setup();

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        concurrent_leave: {
          is_for_current_employer: null,
          leave_start_date: null,
          leave_end_date: null,
        },
      }
    );
  });
});
