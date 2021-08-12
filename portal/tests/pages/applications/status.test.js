import Status from "../../../src/pages/applications/status";
import { renderWithAppLogic } from "../../test-utils";

describe("status page", () => {
  beforeEach(() => {
    process.env.featureFlags = {
      claimantShowStatusPage: true,
    };
  });

  it("displays an error if feature flag is disabled", () => {
    process.env.featureFlags = {
      claimantShowStatusPage: false,
    };
    const { wrapper } = renderWithAppLogic(Status, {
      diveLevels: 0,
    });
    expect(wrapper).toMatchSnapshot();
  });

  it("renders the page", () => {
    const { wrapper } = renderWithAppLogic(Status, {
      diveLevels: 0,
    });
    expect(wrapper).toMatchSnapshot();
  });
});
