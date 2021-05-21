import Success from "../../../../src/pages/employers/applications/success";
import { mockRouter } from "next/router";
import { renderWithAppLogic } from "../../../test-utils";
import routes from "../../../../src/routes";

describe("Success", () => {
  const query = { absence_id: "test-absence-id" };
  let wrapper;

  it("renders Success page", () => {
    ({ wrapper } = renderWithAppLogic(Success, {
      diveLevels: 1,
      props: { query },
    }));

    expect(wrapper).toMatchSnapshot();
  });

  describe("when dashboard feature flag is enabled", () => {
    beforeEach(() => {
      process.env.featureFlags = { employerShowDashboard: true };
    });

    it("renders back button to dashboard", () => {
      mockRouter.pathname = routes.employers.success;
      ({ wrapper } = renderWithAppLogic(Success, {
        diveLevels: 1,
        props: { query },
      }));

      expect(wrapper.find("BackButton")).toMatchSnapshot();
    });

    it("does not render news banner", () => {
      ({ wrapper } = renderWithAppLogic(Success, {
        diveLevels: 1,
        props: { query },
      }));

      expect(wrapper.find("NewsBanner").exists()).toEqual(false);
    });
  });
});
