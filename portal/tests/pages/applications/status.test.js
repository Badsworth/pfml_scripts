import Status, { LeaveDetails } from "../../../src/pages/applications/status";
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

/** Test LeaveDetails component */
// TODO(CP-2482): replace with AbsencePeriodModel
const ABSENCE_DETAIL_LIST = {
  medical: [
    {
      period_type: "Reduced",
      absence_period_start_date: "2021-06-01",
      absence_period_end_date: "2021-06-08",
      request_decision: "Approved",
      fineos_leave_request_id: "PL-14432-0000002026",
    },
    {
      period_type: "Continuous",
      absence_period_start_date: "2021-07-01",
      absence_period_end_date: "2021-07-08",
      request_decision: "Pending",
      fineos_leave_request_id: "PL-14432-0000002326",
    },
  ],
  bonding: [
    {
      period_type: "Reduced",
      absence_period_start_date: "2021-08-01",
      absence_period_end_date: "2021-08-08",
      request_decision: "Denied",
      fineos_leave_request_id: "PL-14434-0000002026",
    },
    {
      period_type: "Continuous",
      absence_period_start_date: "2021-08-01",
      absence_period_end_date: "2021-08-08",
      request_decision: "Withdrawn",
      fineos_leave_request_id: "PL-14434-0000002326",
    },
  ],
};

describe("leave details page", () => {
  it("does not render LeaveDetails if absenceDetails not given", () => {
    const { wrapper } = renderWithAppLogic(LeaveDetails, {
      diveLevels: 0,
      props: { absenceDetails: {} },
    });
    expect(wrapper).toMatchSnapshot();
  });

  it("does renders page separated by keys if object of absenceDetails has more keys", () => {
    const { wrapper } = renderWithAppLogic(LeaveDetails, {
      diveLevels: 0,
      props: { absenceDetails: ABSENCE_DETAIL_LIST },
    });
    expect(wrapper).toMatchSnapshot();
  });

  it("does renders page with one section if absenceDetails has only one key", () => {
    const { wrapper } = renderWithAppLogic(LeaveDetails, {
      diveLevels: 0,
      props: { absenceDetails: { medical: ABSENCE_DETAIL_LIST.medical } },
    });
    expect(wrapper).toMatchSnapshot();
  });
});
