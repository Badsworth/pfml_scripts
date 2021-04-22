import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import FamilyMemberName from "../../../src/pages/applications/family-member-name";
import { pick } from "lodash";

const caringLeavePath = "leave_details.caring_leave_metadata";

const defaultName = {
  leave_details: {
    caring_leave_metadata: {
      family_member_first_name: "Aquib",
      family_member_middle_name: "Cricketer",
      family_member_last_name: "Khan",
    },
  },
};

const setup = (name) => {
  const { appLogic, wrapper } = renderWithAppLogic(FamilyMemberName, {
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

describe("FamilyMemberName", () => {
  it("renders the page", () => {
    const { wrapper } = setup(defaultName);
    expect(wrapper).toMatchSnapshot();
  });

  it("calls claims.update when the form is successfully submitted with pre-filled data", async () => {
    const { appLogic, submitForm } = setup(defaultName);
    const update = jest.spyOn(appLogic.benefitsApplications, "update");

    await submitForm();

    expect(update).toHaveBeenCalledWith(
      expect.any(String),
      pick(defaultName, [
        `${caringLeavePath}.family_member_first_name`,
        `${caringLeavePath}.family_member_last_name`,
        `${caringLeavePath}.family_member_middle_name`,
      ])
    );
  });

  it("calls claims.update when the form is successfully submitted with new data", async () => {
    const { appLogic, changeField, submitForm } = setup({});
    const update = jest.spyOn(appLogic.benefitsApplications, "update");

    const caringLeave = defaultName.leave_details.caring_leave_metadata;

    changeField(
      `${caringLeavePath}.family_member_first_name`,
      caringLeave.family_member_first_name
    );
    changeField(
      `${caringLeavePath}.family_member_middle_name`,
      caringLeave.family_member_middle_name
    );
    changeField(
      `${caringLeavePath}.family_member_last_name`,
      caringLeave.family_member_last_name
    );

    await submitForm();

    expect(update).toHaveBeenCalledWith(
      expect.any(String),
      pick(defaultName, [
        `${caringLeavePath}.family_member_first_name`,
        `${caringLeavePath}.family_member_last_name`,
        `${caringLeavePath}.family_member_middle_name`,
      ])
    );
  });
});
