import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
// import { act, renderHook } from "@testing-library/react-hooks";
import { screen, waitFor } from "@testing-library/react";

// import AppErrorInfo from "../../../src/models/AppErrorInfo";
// import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import OrganizationUnit from "../../../src/pages/applications/department";
// import { searchMock } from "../../../src/api/EmployeesApi";
import { setupBenefitsApplications } from "../../test-utils/helpers";
// import useAppErrorsLogic from "../../../src/hooks/useAppErrorsLogic";
// import useEmployeesLogic from "../../../src/hooks/useEmployeesLogic";
// import usePortalFlow from "../../../src/hooks/usePortalFlow";
import userEvent from "@testing-library/user-event";

// jest.mock("../../../src/api/EmployeesApi");
// jest.mock("../../../src/hooks/useEmployeesLogic");
// jest.mock("../../../src/hooks/useAppLogic");

const goToPageFor = jest.fn(() => {
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

const searchMock = jest.fn();

const setup = (organization_units) => {
  return renderPage(
    OrganizationUnit,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        searchMock.mockImplementation(() => {
          return new Promise((resolve) => {
            resolve({ ...responseData, organization_units });
          });
        });
        appLogic.employees.search = searchMock;
        appLogic.portalFlow.goToPageFor = goToPageFor;
        appLogic.benefitsApplications.update = updateClaim;
      },
    },
    { query }
  );
};

const postData = {
  first_name: claim.first_name || "",
  last_name: claim.last_name || "",
  middle_name: claim.middle_name || "",
  tax_identifier_last4: claim.tax_identifier?.slice(-4) || "",
  employer_fein: claim.employer_fein || "",
};

const employer_id = "a9ec77d6-b459-47ec-bb79-da6082687606";

const responseData = {
  employee_id: "b9ec77d6-b459-47ec-bb79-da6082687606",
  tax_identifier_last4: claim.tax_identifier?.slice(-4) || "",
  first_name: claim.first_name || "",
  last_name: claim.last_name || "",
  middle_name: claim.middle_name || "",
  other_name: null,
  email_address: null,
  phone_number: null,
};

const newOrgUnit = (name, linked) => ({
  organization_unit_id: name.toLowerCase().replace(" ", "_"),
  fineos_id: "PE:00001:00000001",
  name,
  employer_id,
  linked,
});

const singularOrganizationUnitsList = [
  newOrgUnit("Department One", true),
  newOrgUnit("Department Two", false),
];

const shortOrganizationUnitsList = [
  ...singularOrganizationUnitsList,
  newOrgUnit("Department Three", true),
  newOrgUnit("Department Four", false),
];

const longOrganizationUnitsList = [
  ...shortOrganizationUnitsList,
  newOrgUnit("Department Five", true),
  newOrgUnit("Department Six", true),
  newOrgUnit("Department Seven", true),
  newOrgUnit("Department Eight", true),
];

describe("DepartmentPage", () => {
  describe("when claimantShowOrganizationUnits feature flag is disabled", () => {
    beforeEach(() => {
      process.env.featureFlags = {
        claimantShowOrganizationUnits: false,
      };
    });

    it("renders the page", () => {
      const { container } = setup();
      expect(container).toMatchSnapshot();
    });

    it("redirects to next page on first render", async () => {
      setup();
      // First render redirects because feature flag is off
      await waitFor(() => {
        expect(goToPageFor).toHaveBeenCalledTimes(1);
        expect(goToPageFor).toHaveBeenCalledWith("CONTINUE", { claim }, query, {
          redirect: true,
        });
      });
    });
  });

  describe("when claimantShowOrganizationUnits feature flag is enabled", () => {
    beforeEach(() => {
      process.env.featureFlags = {
        claimantShowOrganizationUnits: true,
      };
    });

    it("redirects to next page if department list is empty", async () => {
      setup([]);
      // First render doesn't redirect user because feature flag is on
      await waitFor(() => {
        expect(goToPageFor).toHaveBeenCalledTimes(0);
      });
      // Second render redirects user because units list is empty
      await waitFor(() => {
        expect(goToPageFor).toHaveBeenCalledTimes(1);
      });
    });

    it("doesn't redirect to next page if department list is not empty", async () => {
      setup(singularOrganizationUnitsList);
      // First render doesn't redirect user because feature flag is on
      await waitFor(() => {
        expect(goToPageFor).toHaveBeenCalledTimes(0);
      });
      // Second render doesn't redirect user because units list is not empty
      await waitFor(() => {
        expect(goToPageFor).toHaveBeenCalledTimes(0);
      });
    });

    describe("when there is only one linked department", () => {
      it("renders the page", async () => {
        const { container } = setup(singularOrganizationUnitsList);
        // Wait for multiple component renders
        await waitFor(() => {
          expect(searchMock).toHaveBeenCalledWith(postData);
        });
        expect(container).toMatchSnapshot();
      });

      it("when user selects 'Yes' confirming their deparment submits department", async () => {
        setup(singularOrganizationUnitsList);
        // Wait for multiple component renders
        await waitFor(() => {
          expect(searchMock).toHaveBeenCalledWith(postData);
        });
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
          });
        });
      });

      it("when user selects 'No' picks alternative submits department", async () => {
        setup(singularOrganizationUnitsList);
        // Wait for multiple component renders
        await waitFor(() => {
          expect(searchMock).toHaveBeenCalledWith(postData);
        });
        // Pick a linked department
        const department = singularOrganizationUnitsList[1];
        // Click "No" confirming that "Department One" is not your department
        userEvent.click(screen.getByRole("radio", { name: "No" }));
        // Select an alternative department
        userEvent.type(
          screen.getByRole("combobox", {
            name: "Select a department",
          }),
          department.name + "{enter}" // Needs enter to confirm option in combobox
        );
        // Click Save and continue button
        userEvent.click(
          screen.getByRole("button", { name: "Save and continue" })
        );
        // Check if the PATCH call to update the application was made
        await waitFor(() => {
          expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
            organization_unit_id: department.organization_unit_id,
          });
        });
      });

      it("when user doesn't pick an option cannot submit department", async () => {
        setup(singularOrganizationUnitsList);
        // Wait for multiple component renders
        await waitFor(() => {
          expect(searchMock).toHaveBeenCalledWith(postData);
        });
        // Click Save and continue button
        userEvent.click(
          screen.getByRole("button", { name: "Save and continue" })
        );
        // Shows error to the user
        await waitFor(() => {
          expect(screen.getByRole("alert")).toBeInTheDocument();
        });
        // Click "No" confirming that "Department One" is not your department
        userEvent.click(screen.getByRole("radio", { name: "No" }));
        // Click Save and continue button
        userEvent.click(
          screen.getByRole("button", { name: "Save and continue" })
        );
        // Shows error to the user
        await waitFor(() => {
          expect(screen.getByRole("alert")).toBeInTheDocument();
        });
        // Selects a workaround
        userEvent.type(
          screen.getByRole("combobox", {
            name: "Select a department",
          }),
          "My department is not listed{enter}" // Needs enter to confirm option in combobox
        );
        // Additional information is displayed to the user
        expect(screen.getByRole("region")).toBeInTheDocument();
        // Click Save and continue button
        userEvent.click(
          screen.getByRole("button", { name: "Save and continue" })
        );
        // Check if the PATCH call to update the application was made
        await waitFor(() => {
          expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
            organization_unit_id: null,
          });
        });
        // Clears errors
        expect(screen.getByRole("alert")).not.toBeInTheDocument();
      });
    });

    describe("when there is two to five linked departments", () => {
      it("renders the page", async () => {
        const { container } = setup(shortOrganizationUnitsList);
        // Wait for multiple component renders
        await waitFor(() => {
          expect(searchMock).toHaveBeenCalledWith(postData);
        });
        expect(container).toMatchSnapshot();
      });

      it("when user selects one of the linked departments submits department", async () => {
        setup(shortOrganizationUnitsList);
        // Wait for multiple component renders
        await waitFor(() => {
          expect(searchMock).toHaveBeenCalledWith(postData);
        });
        // Pick a linked department
        const department = shortOrganizationUnitsList[2];
        // Click and confirm your department
        userEvent.click(screen.getByRole("radio", { name: department.name }));
        // Click Save and continue button
        userEvent.click(
          screen.getByRole("button", { name: "Save and continue" })
        );
        // Check if the PATCH call to update the application was made
        await waitFor(() => {
          expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
            organization_unit_id: department.organization_unit_id,
          });
        });
      });

      it("when user picks workaround selects alternative submits department", async () => {
        setup(shortOrganizationUnitsList);
        // Wait for multiple component renders
        await waitFor(() => {
          expect(searchMock).toHaveBeenCalledWith(postData);
        });
        // Pick an unlinked department
        const department = shortOrganizationUnitsList[3];
        // Select a workaround option
        userEvent.click(
          screen.getByRole("radio", { name: "My department is not listed" })
        );
        // Select and confirm your department
        userEvent.type(
          screen.getByRole("combobox", {
            name: "Select a department",
          }),
          department.name + "{enter}" // Needs enter to confirm option in combobox
        );
        // Click Save and continue button
        userEvent.click(
          screen.getByRole("button", { name: "Save and continue" })
        );
        // Check if the PATCH call to update the application was made
        await waitFor(() => {
          expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
            organization_unit_id: department.organization_unit_id,
          });
        });
      });

      // @todo: when user doesn't pick an option cannot submit department
      // @todo: when user picks workaround a warning is displayed
    });

    describe("when there is more than five linked departments", () => {
      it("renders the page", async () => {
        const { container } = setup(longOrganizationUnitsList);
        // Wait for multiple component renders
        await waitFor(() => {
          expect(searchMock).toHaveBeenCalledWith(postData);
        });
        expect(container).toMatchSnapshot();
      });

      it("when user selects a deparment submits department", async () => {
        setup(longOrganizationUnitsList);
        // Wait for multiple component renders
        await waitFor(() => {
          expect(searchMock).toHaveBeenCalledWith(postData);
        });
        // Pick a department
        const department = longOrganizationUnitsList[4];
        // Select and confirm your department
        userEvent.type(
          screen.getByRole("combobox", {
            name: "Select a department",
          }),
          department.name + "{enter}" // Needs enter to confirm option in combobox
        );
        // Click Save and continue button
        userEvent.click(
          screen.getByRole("button", { name: "Save and continue" })
        );
        // Check if the PATCH call to update the application was made
        await waitFor(() => {
          expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
            organization_unit_id: department.organization_unit_id,
          });
        });
      });

      // @todo: when user doesn't pick an option cannot submit department
      // @todo: when user picks workaround a warning is displayed
    });
  });
});
