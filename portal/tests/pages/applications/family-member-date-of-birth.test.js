import BenefitsApplication, {
  CaringLeaveMetadata,
} from "../../../src/models/BenefitsApplication";
import { screen, waitFor } from "@testing-library/react";
import BenefitsApplicationCollection from "../../../src/models/BenefitsApplicationCollection";
import FamilyMemberDateOfBirth from "../../../src/pages/applications/family-member-date-of-birth";
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

  return renderPage(
    FamilyMemberDateOfBirth,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic);
        appLogic.benefitsApplications.update = updateClaim;
        appLogic.benefitsApplications.benefitsApplications =
          new BenefitsApplicationCollection([claim]);
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("FamilyMemberDateOfBirth", () => {
  it("renders the page", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("creates a caring leave metadata object when user submits form", async () => {
    setup();

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        leave_details: {
          caring_leave_metadata: new CaringLeaveMetadata(),
        },
      });
    });
  });

  it("sends other existing caring leave metadata to the API when the user submits form", async () => {
    const FIRST_NAME = "Jane";
    setup({
      leave_details: {
        caring_leave_metadata: { family_member_first_name: FIRST_NAME },
      },
    });

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        leave_details: {
          caring_leave_metadata: new CaringLeaveMetadata({
            family_member_first_name: FIRST_NAME,
          }),
        },
      });
    });
  });

  it("saves date of birth to claim when user submits form", async () => {
    const DATE_OF_BIRTH = "2019-02-28";
    setup();

    const [year, month, day] = DATE_OF_BIRTH.split("-");
    userEvent.type(
      screen.getByRole("textbox", {
        name: "Month",
      }),
      month
    );
    userEvent.type(
      screen.getByRole("textbox", {
        name: "Day",
      }),
      day
    );
    userEvent.type(
      screen.getByRole("textbox", {
        name: "Year",
      }),
      year
    );

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        leave_details: {
          caring_leave_metadata: new CaringLeaveMetadata({
            family_member_date_of_birth: DATE_OF_BIRTH,
          }),
        },
      });
    });
  });
});
