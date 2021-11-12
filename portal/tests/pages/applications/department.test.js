import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { act, renderHook } from "@testing-library/react-hooks";
import { screen, waitFor } from "@testing-library/react";

// import AppErrorInfo from "../../../src/models/AppErrorInfo";
// import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import OrganizationUnit from "../../../src/pages/applications/department";
// import { searchMock } from "../../../src/api/EmployeesApi";
import { setupBenefitsApplications } from "../../test-utils/helpers";
// import useAppErrorsLogic from "../../../src/hooks/useAppErrorsLogic";
// import useEmployeesLogic from "../../../src/hooks/useEmployeesLogic";
// import usePortalFlow from "../../../src/hooks/usePortalFlow";
// import userEvent from "@testing-library/user-event";
import { v4 as uuidv4 } from "uuid";

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

const employer_id = uuidv4();

const responseData = {
  employee_id: uuidv4(),
  tax_identifier_last4: claim.tax_identifier?.slice(-4) || "",
  first_name: claim.first_name || "",
  last_name: claim.last_name || "",
  middle_name: claim.middle_name || "",
  other_name: null,
  email_address: null,
  phone_number: null,
};

const newOrgUnit = (name, linked) => ({
  organization_unit_id: uuidv4(),
  fineos_id: uuidv4(),
  name,
  employer_id,
  linked,
});

const singularOrganizationUnitsList = [
  newOrgUnit("Department One", true),
  newOrgUnit("Department Two", false),
];

const shortOrganizationUnitsList = [
  newOrgUnit("Department One", true),
  newOrgUnit("Department Two", true),
  newOrgUnit("Department Three", false),
  newOrgUnit("Department Four", false),
];

const longOrganizationUnitsList = [
  newOrgUnit("Department One", true),
  newOrgUnit("Department Two", true),
  newOrgUnit("Department Three", true),
  newOrgUnit("Department Four", true),
  newOrgUnit("Department Five", true),
  newOrgUnit("Department Six", true),
  newOrgUnit("Department Seven", false),
];

describe("DepartmentPage", () => {
  describe("when claimantShowOrganizationUnits feature flag is disabled", () => {
    beforeEach(() => {
      process.env.featureFlags = {
        claimantShowOrganizationUnits: false,
      };
    });

    it("renders the page without the department fields", () => {
      const { container } = setup();
      expect(container).toMatchSnapshot();
    });

    it("redirects to next page", () => {
      setup();
      expect(goToPageFor).toHaveBeenCalledTimes(1);
      expect(goToPageFor).toHaveBeenCalledWith("CONTINUE", { claim }, query, {
        redirect: true,
      });
    });
  });

  describe("when claimantShowOrganizationUnits feature flag is enabled", () => {
    beforeEach(() => {
      process.env.featureFlags = {
        claimantShowOrganizationUnits: true,
      };
    });

    it("does not redirect to next page", () => {
      setup([]); // @todo: this should be failing due to zero org units but it isn't
      expect(goToPageFor).toHaveBeenCalledTimes(0);
    });

    it("renders the page with one linked organization unit", async () => {
      const { container } = setup(singularOrganizationUnitsList);
      await waitFor(() => {
        expect(searchMock).toHaveBeenCalledWith(postData);
      });
      expect(container).toMatchSnapshot();
    });

    it("renders the page with two to five linked organization units", async () => {
      const { container } = setup(shortOrganizationUnitsList);
      await waitFor(() => {
        expect(searchMock).toHaveBeenCalledWith(postData);
      });
      expect(container).toMatchSnapshot();
    });

    it("renders the page with more than five linked organization units", async () => {
      const { container } = setup(longOrganizationUnitsList);
      await waitFor(() => {
        expect(searchMock).toHaveBeenCalledWith(postData);
      });
      expect(container).toMatchSnapshot();
    });

    // @todo: More tests going through the UI, selecting a department and saving it
  });
});
