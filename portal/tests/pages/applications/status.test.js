import Status from "../../../src/pages/applications/status";
import { renderWithAppLogic } from "../../test-utils";
import routes from "../../../src/routes";

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

  it("does not render ViewYourNotices if documents not given", () => {
    const { wrapper } = renderWithAppLogic(Status, {
      diveLevels: 0,
      props: { docList: [] },
    });
    expect(wrapper).toMatchSnapshot();
  });

  it("does not render LeaveDetails if absenceDetails not given", () => {
    const { wrapper } = renderWithAppLogic(Status, {
      diveLevels: 0,
      props: { absenceDetails: {} },
    });
    expect(wrapper).toMatchSnapshot();
  });

  it("includes a button to upload additional documents", () => {
    const { wrapper } = renderWithAppLogic(Status, {
      diveLevels: 0,
    });

    const button = wrapper.find("ButtonLink");
    expect(button.children().text()).toEqual("Upload additional documents");
    expect(button.exists()).toBe(true);
    expect(wrapper).toMatchSnapshot();
    /* // TODO (CP-2457): remove hard coded claim_id, update to claim.application_id */
    expect(button.prop("href")).toBe(
      `${routes.applications.uploadDocsOptions}?claim_id=65184a9e-f938-40b6-b0f6-25f416a4c113`
    );
  });
});
