import { renderWithAppLogic, simulateEvents } from "../../../test-utils";
import AddOrganization from "../../../../src/pages/employers/organizations/add-organization";
import routes from "../../../../src/routes";

jest.mock("../../../../src/hooks/useAppLogic");

describe("AddOrganization", () => {
  let appLogic, changeField, submitForm, wrapper;

  describe('when "employerShowAddOrganization" is enabled', () => {
    beforeEach(() => {
      process.env.featureFlags = { employerShowAddOrganization: true };
      ({ wrapper, appLogic } = renderWithAppLogic(AddOrganization, {
        diveLevels: 1,
      }));
    });

    it("renders the page", () => {
      expect(wrapper).toMatchSnapshot();
      expect(appLogic.portalFlow.goTo).not.toHaveBeenCalled();
    });

    it("submits FEIN", async () => {
      ({ changeField, submitForm } = simulateEvents(wrapper));
      changeField("ein", "012345678");
      await submitForm();

      expect(appLogic.employers.addEmployer).toHaveBeenCalledWith(
        {
          employer_fein: "012345678",
        },
        routes.employers.organizations
      );
    });
  });

  describe('when "employerShowAddOrganization" is disabled', () => {
    beforeEach(() => {
      process.env.featureFlags = { employerShowAddOrganization: false };
      ({ appLogic } = renderWithAppLogic(AddOrganization, {
        diveLevels: 1,
      }));
    });

    it("redirects to Welcome page", () => {
      expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
        routes.employers.welcome
      );
    });
  });
});
