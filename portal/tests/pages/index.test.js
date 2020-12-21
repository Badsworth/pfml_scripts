import { Auth } from "@aws-amplify/auth";
import Index from "../../src/pages/index";
import { act } from "react-dom/test-utils";
import { renderWithAppLogic } from "../test-utils";

jest.mock("@aws-amplify/auth");
jest.mock("../../src/hooks/useAppLogic");

describe("Index", () => {
  it("renders pre-launch index content", () => {
    const { wrapper } = renderWithAppLogic(Index, {
      diveLevels: 0,
    });
    expect(wrapper).toMatchSnapshot();
    wrapper
      .find("Trans")
      .forEach((trans) => expect(trans.dive()).toMatchSnapshot());
  });

  it("renders post-launch index content when claimantShowAuth is true", () => {
    process.env.featureFlags = { claimantShowAuth: true };
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

    it("redirects to dashboard", async () => {
      const { appLogic, wrapper } = renderWithAppLogic(Index, {
        diveLevels: 0,
        render: "mount",
      });
      await act(async () => {
        await wrapper.update();
      });

      expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith("/dashboard");
    });
  });

  describe("when user is not logged in", () => {
    beforeEach(() => {
      Auth.currentUserInfo.mockResolvedValue();
    });

    it("does not redirect to dashboard", async () => {
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
