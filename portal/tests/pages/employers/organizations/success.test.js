import Success from "../../../../src/pages/employers/organizations/success";
import { UserLeaveAdministrator } from "../../../../src/models/User";
import { renderWithAppLogic } from "../../../test-utils";

jest.mock("../../../../src/hooks/useAppLogic");

describe("Success", () => {
  const query = {
    employer_id: "mock_employer_id",
    next: "/employers/organizations",
  };
  let appLogic, wrapper;

  const renderPage = (query) => {
    ({ wrapper, appLogic } = renderWithAppLogic(Success, {
      diveLevels: 1,
      props: { query },
      userAttrs: {
        user_leave_administrators: [
          new UserLeaveAdministrator({
            employer_dba: "Company Name",
            employer_fein: "11-111111",
            employer_id: "mock_employer_id",
            verified: false,
          }),
        ],
      },
    }));
  };

  it("renders the page", () => {
    renderPage(query);

    expect(wrapper).toMatchSnapshot();
    wrapper.find("Trans").forEach((trans) => {
      expect(trans.dive()).toMatchSnapshot();
    });
  });

  describe("upon clicking 'Continue' button", () => {
    it("navigates to Organizations page", () => {
      renderPage(query);

      wrapper.find("Button").simulate("click");
      expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
        "/employers/organizations"
      );
    });

    it("navigates to Organizations page by default if query param is invalid", () => {
      const queryWithoutNextParam = {
        employer_id: "mock_employer_id",
        next: "",
      };
      renderPage(queryWithoutNextParam);

      wrapper.find("Button").simulate("click");
      expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
        "/employers/organizations"
      );
    });

    it("navigates to New Application page based on next param", () => {
      const queryWithNextParam = {
        employer_id: "mock_employer_id",
        next: "/employers/applications/new-application/?absence_id=mock_absence_id",
      };
      renderPage(queryWithNextParam);

      wrapper.find("Button").simulate("click");
      expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
        "/employers/applications/new-application/?absence_id=mock_absence_id"
      );
    });
  });
});
