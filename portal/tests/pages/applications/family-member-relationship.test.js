import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import FamilyMemberRelationship from "../../../src/pages/applications/family-member-relationship";

const setup = (claimAttrs = {}) => {
  const {
    appLogic,
    claim,
    wrapper,
  } = renderWithAppLogic(FamilyMemberRelationship, { claimAttrs });

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

  it("calls claims.update when user submits form with newly-entered relationship data", async () => {
    const { appLogic, changeRadioGroup, claim, submitForm } = setup();
    const spy = jest.spyOn(appLogic.benefitsApplications, "update");

    changeRadioGroup(
      "leave_details.caring_leave_metadata.relationship_to_caregiver",
      "Child"
    );

    await submitForm();
    expect(spy).toHaveBeenCalledWith(claim.application_id, {
      leave_details: {
        caring_leave_metadata: {
          relationship_to_caregiver: "Child",
        },
      },
    });
  });

  it("calls claims.update when the form is successfully submitted with pre-filled data", async () => {
    const { appLogic, claim, submitForm } = setup({
      leave_details: {
        caring_leave_metadata: { relationship_to_caregiver: "Child" },
      },
    });
    const spy = jest.spyOn(appLogic.benefitsApplications, "update");
    await submitForm();

    expect(spy).toHaveBeenCalledWith(claim.application_id, {
      leave_details: {
        caring_leave_metadata: {
          relationship_to_caregiver: "Child",
        },
      },
    });
  });
});
