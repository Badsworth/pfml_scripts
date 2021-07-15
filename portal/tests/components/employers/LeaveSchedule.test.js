import { MockEmployerClaimBuilder, renderWithAppLogic } from "../../test-utils";
import LeaveSchedule from "../../../src/components/employers/LeaveSchedule";

jest.mock("../../../src/hooks/useAppLogic");

const COMPLETED_CLAIM = new MockEmployerClaimBuilder().completed().create();
const INTERMITTENT_CLAIM = new MockEmployerClaimBuilder()
  .intermittent()
  .absenceId()
  .create();

describe("LeaveSchedule", () => {
  let wrapper;

  const renderWithClaim = (claim, render = "shallow", hasDocuments = false) => {
    ({ wrapper } = renderWithAppLogic(LeaveSchedule, {
      diveLevels: 0,
      employerClaimAttrs: claim,
      props: {
        absenceId: "NTN-111-ABS-01",
        claim,
        hasDocuments,
      },
      render,
    }));
  };

  beforeEach(() => {
    renderWithClaim(COMPLETED_CLAIM);
  });

  it("renders continuous schedule", () => {
    const continuousClaim = new MockEmployerClaimBuilder()
      .continuous()
      .absenceId()
      .create();
    renderWithClaim(continuousClaim);
    const cellValues = wrapper
      .find("tbody")
      .find("tr")
      .children()
      .map((cell) => cell.text());

    expect(cellValues).toEqual(["1/1/2021 – 6/1/2021", "Continuous leave"]);
    expect(wrapper).toMatchSnapshot();
  });

  it("renders intermittent schedule", () => {
    renderWithClaim(INTERMITTENT_CLAIM);
    expect(wrapper.find("IntermittentLeaveSchedule").exists()).toEqual(true);
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").last().dive()).toMatchSnapshot();
  });

  it("renders reduced schedule", () => {
    const reducedScheduleClaim = new MockEmployerClaimBuilder()
      .reducedSchedule()
      .absenceId()
      .create();
    renderWithClaim(reducedScheduleClaim);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").last().dive()).toMatchSnapshot();
  });

  it("renders multiple schedule types", () => {
    const multipleSchedulesClaim = new MockEmployerClaimBuilder()
      .continuous()
      .intermittent()
      .reducedSchedule()
      .absenceId()
      .create();

    renderWithClaim(multipleSchedulesClaim, "mount");
    const rows = wrapper.find("tbody").find("tr");
    // if previous three tests pass, assume that the three rows correspond to the three types
    expect(rows.length).toEqual(3);
  });

  describe("when there are documents", () => {
    beforeEach(() => {
      ({ wrapper } = renderWithAppLogic(LeaveSchedule, {
        diveLevels: 0,
        employerClaimAttrs: COMPLETED_CLAIM,
        props: {
          absenceId: "NTN-111-ABS-01",
          claim: COMPLETED_CLAIM,
          hasDocuments: true,
        },
      }));
    });

    it("displays help text for a non-intermittent schedule with documents", () => {
      expect(wrapper.find("p").find("Trans").dive().text()).toEqual(
        "This is your employee’s expected leave schedule. Download the attached documentation for more details."
      );
    });
  });

  describe("when there are documents for intermittent schedule", () => {
    beforeEach(() => {
      ({ wrapper } = renderWithAppLogic(LeaveSchedule, {
        diveLevels: 0,
        employerClaimAttrs: INTERMITTENT_CLAIM,
        props: {
          absenceId: "NTN-111-ABS-01",
          claim: INTERMITTENT_CLAIM,
          hasDocuments: true,
        },
      }));
    });

    it("displays help text for an intermittent schedule with documents", () => {
      expect(wrapper.find("p").find("Trans").dive().text()).toEqual(
        "Download the attached documentation for details about the employee’s intermittent leave schedule."
      );
    });
  });

  describe("when there are no documents", () => {
    beforeEach(() => {
      ({ wrapper } = renderWithAppLogic(LeaveSchedule, {
        diveLevels: 0,
        employerClaimAttrs: COMPLETED_CLAIM,
        props: {
          absenceId: "NTN-111-ABS-01",
          claim: COMPLETED_CLAIM,
        },
      }));
    });

    it("displays help text for a schedule without documents", () => {
      expect(wrapper.find("p").find("Trans").dive().text()).toEqual(
        "This is your employee’s expected leave schedule."
      );
    });
  });
});
