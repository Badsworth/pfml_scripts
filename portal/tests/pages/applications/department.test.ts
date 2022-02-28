import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";

import Department from "../../../src/pages/applications/department";
import OrganizationUnit from "../../../src/models/OrganizationUnit";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

// Mock data
const goToNextPage = jest.fn(() => {
  return Promise.resolve();
});

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});

const query = { claim_id: "mock_application_id" };

const claim = new MockBenefitsApplicationBuilder()
  .verifiedId()
  .employed()
  .create();

const newOrgUnit = (name: string) => ({
  organization_unit_id: name.toLowerCase().replace(" ", "_"),
  name,
});

const defaultEmployerOrgUnits = [
  newOrgUnit("Department One"),
  newOrgUnit("Department Two"),
  newOrgUnit("Department Three"),
  newOrgUnit("Department Four"),
  newOrgUnit("Department Five"),
  newOrgUnit("Department Six"),
  newOrgUnit("Department Seven"),
  newOrgUnit("Department Eight"),
];

const singularOrganizationUnitsList = [defaultEmployerOrgUnits[0]];
const longOrganizationUnitsList = [
  defaultEmployerOrgUnits[0],
  defaultEmployerOrgUnits[1],
  defaultEmployerOrgUnits[2],
  defaultEmployerOrgUnits[3],
  defaultEmployerOrgUnits[4],
  defaultEmployerOrgUnits[5],
];

// Render page
const setup = (
  employeeOrgUnits: OrganizationUnit[] = [],
  useDefaultEmployerOrgUnits = true
) => {
  // Setup claim org units
  claim.employee_organization_units = employeeOrgUnits;
  // Add default employer org units (otherwise this page wouldn't exist)
  claim.employer_organization_units = useDefaultEmployerOrgUnits
    ? defaultEmployerOrgUnits
    : [];
  return renderPage(
    Department,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        appLogic.portalFlow.goToNextPage = goToNextPage;
        appLogic.benefitsApplications.update = updateClaim;
      },
    },
    { query }
  );
};

describe("DepartmentPage", () => {
  describe("when claimantShowOrganizationUnits feature flag is disabled", () => {
    beforeEach(() => {
      process.env.featureFlags = JSON.stringify({
        claimantShowOrganizationUnits: false,
      });
    });

    it("redirects to next page", async () => {
      setup();
      // Redirects because feature flag is off
      await waitFor(() => {
        expect(goToNextPage).toHaveBeenCalledTimes(1);
        expect(goToNextPage).toHaveBeenCalledWith(
          { claim },
          { claim_id: claim.application_id }
        );
      });
    });
  });

  describe("when claimantShowOrganizationUnits feature flag is enabled", () => {
    beforeEach(() => {
      process.env.featureFlags = JSON.stringify({
        claimantShowOrganizationUnits: true,
      });
    });

    it("redirects to next page if department list is empty", async () => {
      setup([], false);
      // Redirects because department list is empty
      await waitFor(() => {
        expect(goToNextPage).toHaveBeenCalledTimes(1);
        expect(goToNextPage).toHaveBeenCalledWith(
          { claim },
          { claim_id: claim.application_id }
        );
      });
    });

    it("doesn't redirect to next page if department list is not empty", async () => {
      setup();
      // Doesn't redirect because employer department list is not empty
      await waitFor(() => {
        expect(goToNextPage).toHaveBeenCalledTimes(0);
      });
    });

    it("renders the confirmation page", () => {
      const { container } = setup(singularOrganizationUnitsList);
      expect(container).toMatchSnapshot();
    });

    it("renders the page with a long list", () => {
      const { container } = setup(longOrganizationUnitsList);
      expect(container).toMatchSnapshot();
    });

    it("submits org unit id when user selects 'Yes'", async () => {
      setup(singularOrganizationUnitsList);
      // Pick a linked department
      const department = singularOrganizationUnitsList[0];
      // Click "Yes" confirming "Department One" as your department
      userEvent.click(screen.getByRole("radio", { name: "Yes" }));
      // Click Save and continue button
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      // Check if the PATCH call to update the application was made
      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
          organization_unit_id: department.organization_unit_id,
          organization_unit_selection: null,
        });
      });
    });

    it("submits alternative org unit id when user selects 'No'", async () => {
      setup(singularOrganizationUnitsList);
      // Pick an unlinked department
      const department = defaultEmployerOrgUnits[1];
      // Click "No" confirming that "Department One" is not your department
      userEvent.click(screen.getByRole("radio", { name: "No" }));
      // Select an alternative department
      userEvent.type(
        screen.getByRole(
          "combobox",
          {
            name: "Select your department",
          },
          { hidden: true }
        ),
        department.name + "{enter}" // Needs {enter} to confirm option in combobox
      );
      // Click Save and continue button
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      // Check if the PATCH call to update the application was made
      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
          organization_unit_id: department.organization_unit_id,
          organization_unit_selection: null,
        });
      });
    });

    it("submits org unit selection when user selects 'No'", async () => {
      setup(singularOrganizationUnitsList);
      // Pick a workaround
      const workaround = "not sure";
      // Click "No" confirming that "Department One" is not your department
      userEvent.click(screen.getByRole("radio", { name: "No" }));
      // Select and confirm your workaround
      userEvent.type(
        screen.getByRole("combobox", {
          name: "Select your department",
        }),
        workaround + "{arrowdown}{enter}" // Needs {enter} to confirm option in combobox
      );
      // Click Save and continue button
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      // Check if the PATCH call to update the application was made
      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
          organization_unit_id: null,
          organization_unit_selection: "not_selected",
        });
      });
    });

    it("submits org unit id when a department is selected", async () => {
      setup(longOrganizationUnitsList);
      // Pick a department
      const department = longOrganizationUnitsList[4];
      // Select and confirm your department
      userEvent.type(
        screen.getByRole("combobox", {
          name: "Select your department",
        }),
        department.name + "{enter}" // Needs {enter} to confirm option in combobox
      );
      // Click Save and continue button
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      // Check if the PATCH call to update the application was made
      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
          organization_unit_id: department.organization_unit_id,
          organization_unit_selection: null,
        });
      });
    });

    it("submits org unit selection when a workaround is selected", async () => {
      setup(longOrganizationUnitsList);
      // Pick a workaround
      const workaround = "not sure";
      // Select and confirm your workaround
      userEvent.type(
        screen.getByRole("combobox", {
          name: "Select your department",
        }),
        workaround + "{arrowdown}{enter}" // Needs {enter} to confirm option in combobox
      );
      // Click Save and continue button
      userEvent.click(
        screen.getByRole("button", { name: "Save and continue" })
      );
      // Check if the PATCH call to update the application was made
      await waitFor(() => {
        expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
          organization_unit_id: null,
          organization_unit_selection: "not_selected",
        });
      });
    });
  });
});
