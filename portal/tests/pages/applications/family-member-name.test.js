import { screen, waitFor } from "@testing-library/react";
import BenefitsApplication from "../../../src/models/BenefitsApplication";
import FamilyMemberName from "../../../src/pages/applications/family-member-name";
import { pick } from "lodash";
import { renderPage } from "../../test-utils";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

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

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});

const setup = (name) => {
  const claimAttrs = {
    ...name,
  };
  const claim = new BenefitsApplication({
    application_id: "mock_application_id",
    ...claimAttrs,
  });
  const cb = (appLogic) => {
    appLogic.benefitsApplications.update = updateClaim;
  };
  return renderPage(
    FamilyMemberName,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim], cb);
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("FamilyMemberName", () => {
  it("renders the page", () => {
    const { container } = setup(defaultName);
    expect(container).toMatchSnapshot();
  });

  it("calls claims.update when the form is successfully submitted with pre-filled data", async () => {
    setup(defaultName);

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith(
        expect.any(String),
        pick(defaultName, [
          `${caringLeavePath}.family_member_first_name`,
          `${caringLeavePath}.family_member_last_name`,
          `${caringLeavePath}.family_member_middle_name`,
        ])
      );
    });
  });

  it("calls claims.update when the form is successfully submitted with new data", async () => {
    setup();

    const caringLeave = defaultName.leave_details.caring_leave_metadata;
    userEvent.type(
      screen.getByRole("textbox", { name: "First name" }),
      caringLeave.family_member_first_name
    );
    userEvent.type(
      screen.getByRole("textbox", { name: "Middle name (optional)" }),
      caringLeave.family_member_middle_name
    );
    userEvent.type(
      screen.getByRole("textbox", { name: "Last name" }),
      caringLeave.family_member_last_name
    );

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith(
        expect.any(String),
        pick(defaultName, [
          `${caringLeavePath}.family_member_first_name`,
          `${caringLeavePath}.family_member_last_name`,
          `${caringLeavePath}.family_member_middle_name`,
        ])
      );
    });
  });
});
