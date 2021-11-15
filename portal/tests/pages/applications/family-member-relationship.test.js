import { screen, waitFor } from "@testing-library/react";
import BenefitsApplication from "../../../src/models/BenefitsApplication";
import FamilyMemberRelationship from "../../../src/pages/applications/family-member-relationship";
import { renderPage } from "../../test-utils";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});

const setup = (claimAttrs = {}) => {
  const claim = new BenefitsApplication({
    application_id: "mock_application_id",
    ...claimAttrs,
  });
  const cb = (appLogic) => {
    appLogic.benefitsApplications.update = updateClaim;
  };
  return renderPage(
    FamilyMemberRelationship,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim], cb);
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("FamilyMemberRelationship", () => {
  it("renders the page", () => {
    const { container } = setup();

    expect(container).toMatchSnapshot();
  });

  it("calls claims.update when user submits form with newly-entered relationship data", async () => {
    setup();
    userEvent.click(
      screen.getByRole("radio", { name: "I am caring for my child." })
    );
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        leave_details: {
          caring_leave_metadata: {
            relationship_to_caregiver: "Child",
          },
        },
      });
    });
  });

  it("calls claims.update when the form is successfully submitted with pre-filled data", async () => {
    setup({
      leave_details: {
        caring_leave_metadata: { relationship_to_caregiver: "Child" },
      },
    });
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        leave_details: {
          caring_leave_metadata: {
            relationship_to_caregiver: "Child",
          },
        },
      });
    });
  });
});
