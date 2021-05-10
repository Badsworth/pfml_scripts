import { Auth } from "@aws-amplify/auth";
import Index from "../../src/pages/index";
import { act } from "react-dom/test-utils";
import { renderWithAppLogic } from "../test-utils";

jest.mock("@aws-amplify/auth");
jest.mock("../../src/hooks/useAppLogic");

describe("Index", () => {
  it("renders landing page content", () => {
    const { wrapper } = renderWithAppLogic(Index, {
      diveLevels: 0,
    });
    expect(wrapper).toMatchSnapshot();
    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });

  it("does show employer information when employerShowSelfRegistrationForm is true", () => {
    process.env.featureFlags = { employerShowSelfRegistrationForm: true };
    const { wrapper } = renderWithAppLogic(Index, {
      diveLevels: 0,
    });

    expect(wrapper).toMatchSnapshot();
    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });

  describe("when user is logged in", () => {
    beforeEach(() => {
      Auth.currentUserInfo.mockResolvedValue({
        attributes: {
          email: "test@email.com",
        },
      });
    });

    it("redirects to applications", async () => {
      const { appLogic, wrapper } = renderWithAppLogic(Index, {
        diveLevels: 0,
        render: "mount",
      });

      await act(async () => {
        await wrapper.update();
      });

      expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith("/applications");
    });
  });

  describe("when user is not logged in", () => {
    beforeEach(() => {
      Auth.currentUserInfo.mockResolvedValue();
    });

    it("does not redirect to applications", async () => {
      const { appLogic, wrapper } = renderWithAppLogic(Index, {
        diveLevels: 0,
        render: "mount",
      });

      await act(async () => {
        // Wait for repaint
        await new Promise((resolve) => setTimeout(resolve, 0));
      });

      wrapper.update();

      expect(appLogic.portalFlow.goTo).not.toHaveBeenCalled();
    });
  });
});
