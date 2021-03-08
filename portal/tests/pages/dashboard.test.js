import Dashboard from "../../src/pages/dashboard";
import { act } from "react-dom/test-utils";
import { renderWithAppLogic } from "../test-utils";

jest.mock("@aws-amplify/auth");
jest.mock("../../src/hooks/useAppLogic");

describe("Dashboard", () => {
  it("redirects to getReady", async () => {
    const { appLogic, wrapper } = renderWithAppLogic(Dashboard, {
      diveLevels: 0,
      render: "mount",
    });

    await act(async () => {
      await wrapper.update();
    });

    expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
      "/applications/get-ready"
    );
  });
});
