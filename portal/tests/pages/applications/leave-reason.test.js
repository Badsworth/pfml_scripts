import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import LeaveReason from "../../../src/models/LeaveReason";
import LeaveReasonPage from "../../../src/pages/applications/leave-reason";
import { ReasonQualifier } from "../../../src/models/BenefitsApplication";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claim = new MockBenefitsApplicationBuilder().create()) => {
  const { appLogic, wrapper } = renderWithAppLogic(LeaveReasonPage, {
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

const medicalLeaveClaim = new MockBenefitsApplicationBuilder()
  .medicalLeaveReason()
  .create();
const caringLeaveClaim = new MockBenefitsApplicationBuilder()
  .caringLeaveReason()
  .create();

describe("LeaveReasonPage", () => {
  it("renders the page with all five reasons when type feature flags are enabled", () => {
    process.env.featureFlags = {
      claimantShowMilitaryLeaveTypes: true,
      showCaringLeaveType: true,
    };

    const { wrapper } = setup();

    const choiceGroup = wrapper.find("InputChoiceGroup").first().dive();

    expect(choiceGroup.exists(`[value="${LeaveReason.medical}"]`)).toBe(true);
    expect(choiceGroup.exists(`[value="${LeaveReason.bonding}"]`)).toBe(true);
    expect(choiceGroup.exists(`[value="${LeaveReason.care}"]`)).toBe(true);
    expect(
      choiceGroup.exists(`[value="${LeaveReason.activeDutyFamily}"]`)
    ).toBe(true);
    expect(
      choiceGroup.exists(`[value="${LeaveReason.serviceMemberFamily}"]`)
    ).toBe(true);
  });

  it("renders the page without military leave and caring leave options when type feature flags are disabled", () => {
    process.env.featureFlags = {
      claimantShowMilitaryLeaveTypes: false,
      showCaringLeaveType: false,
    };

    const { wrapper } = setup();

    const choiceGroup = wrapper.find("InputChoiceGroup").first().dive();

    expect(choiceGroup.exists(`[value="${LeaveReason.medical}"]`)).toBe(true);
    expect(choiceGroup.exists(`[value="${LeaveReason.bonding}"]`)).toBe(true);
    expect(choiceGroup.exists(`[value="${LeaveReason.care}"]`)).toBe(false);
    expect(
      choiceGroup.exists(`[value="${LeaveReason.activeDutyFamily}"]`)
    ).toBe(false);
    expect(
      choiceGroup.exists(`[value="${LeaveReason.serviceMemberFamily}"]`)
    ).toBe(false);
  });

  it("renders the page for medical leave and does not show reason qualifier followup", () => {
    const { wrapper } = setup(medicalLeaveClaim);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
    expect(
      wrapper
        .find({ name: "leave_details.reason_qualifier" })
        .parents("ConditionalContent")
        .prop("visible")
    ).toBe(false);
  });

  it("renders the page for caring leave and does not show reason qualifier followup", () => {
    const { wrapper } = setup(caringLeaveClaim);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
    expect(
      wrapper
        .find({ name: "leave_details.reason_qualifier" })
        .parents("ConditionalContent")
        .prop("visible")
    ).toBe(false);
  });

  it("shows the bonding type question when a user selects bonding as their leave reason", () => {
    const { changeRadioGroup, wrapper } = setup();

    changeRadioGroup("leave_details.reason", LeaveReason.bonding);

    expect(
      wrapper
        .find({ name: "leave_details.reason_qualifier" })
        .parents("ConditionalContent")
        .prop("visible")
    ).toBe(true);
  });

  it("calls claims.update with leave reason and reason qualifier for bonding leave when the user selects those options", async () => {
    const { appLogic, changeRadioGroup, claim, submitForm } = setup();

    changeRadioGroup("leave_details.reason", LeaveReason.bonding);
    changeRadioGroup("leave_details.reason_qualifier", ReasonQualifier.newBorn);

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        leave_details: {
          reason: LeaveReason.bonding,
          reason_qualifier: ReasonQualifier.newBorn,
        },
      }
    );
  });

  it("calls claims.update with with only leave reason for medical leave and set child birth/placement date to null", async () => {
    const { appLogic, submitForm } = setup(medicalLeaveClaim);

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      medicalLeaveClaim.application_id,
      {
        leave_details: {
          child_birth_date: null,
          child_placement_date: null,
          has_future_child_date: null,
          reason: LeaveReason.medical,
          reason_qualifier: null,
        },
      }
    );
  });

  it("calls claims.update with with only leave reason for caring leave and set child birth/placement date to null", async () => {
    const { appLogic, submitForm } = setup(caringLeaveClaim);

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      medicalLeaveClaim.application_id,
      {
        leave_details: {
          child_birth_date: null,
          child_placement_date: null,
          has_future_child_date: null,
          reason: LeaveReason.care,
          reason_qualifier: null,
        },
      }
    );
  });

  it("sets the radio values and calls claims.update with leave reason and reason qualifer when the claim already has data", async () => {
    const bondingFosterCareClaim = new MockBenefitsApplicationBuilder()
      .bondingFosterCareLeaveReason()
      .create();

    const { appLogic, claim, wrapper } = setup(bondingFosterCareClaim);

    const bondingReasonRadio = wrapper
      .find("InputChoiceGroup")
      .first()
      .dive()
      .find({ value: LeaveReason.bonding });
    expect(bondingReasonRadio.props().checked).toBe(true);

    const fosterQualifierRadio = wrapper
      .find("ConditionalContent")
      .dive()
      .find("InputChoiceGroup")
      .first()
      .dive()
      .find({ value: ReasonQualifier.fosterCare });
    expect(fosterQualifierRadio.props().checked).toBe(true);

    const { submitForm } = simulateEvents(wrapper);

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        leave_details: {
          reason: LeaveReason.bonding,
          reason_qualifier: ReasonQualifier.fosterCare,
        },
      }
    );
  });
});
