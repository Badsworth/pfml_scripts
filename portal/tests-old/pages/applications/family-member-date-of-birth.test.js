import { renderWithAppLogic, simulateEvents } from "../../test-utils";
import { CaringLeaveMetadata } from "../../../src/models/BenefitsApplication";
import FamilyMemberDateOfBirth from "../../../src/pages/applications/family-member-date-of-birth";

jest.mock("../../../src/hooks/useAppLogic");

const setup = (claimAttrs = {}) => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(
    FamilyMemberDateOfBirth,
    { claimAttrs }
  );

  const { changeField, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeField,
    claim,
    submitForm,
    wrapper,
  };
};

describe("FamilyMemberDateOfBirth", () => {
  it("renders the page", () => {
    const { wrapper } = setup();

    expect(wrapper).toMatchSnapshot();
  });

  it("creates a caring leave metadata object when user submits form", async () => {
    const { appLogic, claim, submitForm } = setup();

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        leave_details: {
          caring_leave_metadata: new CaringLeaveMetadata(),
        },
      }
    );
  });

  it("sends other existing caring leave metadata to the API when the user submits form", async () => {
    const FIRST_NAME = "Jane";
    const { appLogic, claim, submitForm } = setup({
      leave_details: {
        caring_leave_metadata: { family_member_first_name: FIRST_NAME },
      },
    });

    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        leave_details: {
          caring_leave_metadata: new CaringLeaveMetadata({
            family_member_first_name: FIRST_NAME,
          }),
        },
      }
    );
  });

  it("saves date of birth to claim when user submits form", async () => {
    const DATE_OF_BIRTH = "2019-02-28";
    const { appLogic, claim, changeField, submitForm } = setup();

    changeField(
      "leave_details.caring_leave_metadata.family_member_date_of_birth",
      DATE_OF_BIRTH
    );
    await submitForm();

    expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
      claim.application_id,
      {
        leave_details: {
          caring_leave_metadata: new CaringLeaveMetadata({
            family_member_date_of_birth: DATE_OF_BIRTH,
          }),
        },
      }
    );
  });
});
