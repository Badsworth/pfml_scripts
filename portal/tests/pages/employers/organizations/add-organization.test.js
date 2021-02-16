import AddOrganization from "../../../../src/pages/employers/organizations/add-organization";
import { renderWithAppLogic } from "../../../test-utils";
import routes from "../../../../src/routes";

jest.mock("../../../../src/hooks/useAppLogic");

describe("AddOrganization", () => {
  let appLogic, wrapper;

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
        routes.employers.dashboard
      );
    });
  });
});
