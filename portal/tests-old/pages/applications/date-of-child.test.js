import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import DateOfChild from "../../../src/pages/applications/date-of-child";
import { DateTime } from "luxon";
import { ReasonQualifier } from "../../../src/models/BenefitsApplication";

jest.mock("../../../src/hooks/useAppLogic");

const past = DateTime.local().minus({ months: 1 }).toISODate();
const now = DateTime.local().toISODate();
const future = DateTime.local().plus({ months: 1 }).toISODate();

const child_birth_date = "leave_details.child_birth_date";
const child_placement_date = "leave_details.child_placement_date";

const setup = (claimAttrs) => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(DateOfChild, {
    claimAttrs,
  });

  const { changeField, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    changeField,
    claim,
    submitForm,
    wrapper,
  };
};

describe("DateOfChild", () => {
  it("renders the page", () => {
    const { wrapper } = setup();
    expect(wrapper).toMatchSnapshot();
  });

  it("shows the birth date input with hint text when the claim is for a newborn", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .bondingBirthLeaveReason()
      .create();
    const { wrapper } = setup(claim);

    expect(wrapper.find({ name: child_birth_date }).exists()).toBeTruthy();
    expect(wrapper.find({ name: child_placement_date }).exists()).toBeFalsy();
    expect(wrapper.find("InputDate").prop("hint")).toMatchInlineSnapshot(
      `"If your child has not been born yet, enter the expected due date."`
    );
  });

  it("shows the correct input question when the claim is for an adoption", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .bondingAdoptionLeaveReason()
      .create();
    const { wrapper } = setup(claim);

    expect(wrapper.find({ name: child_placement_date }).exists()).toBeTruthy();
    expect(wrapper.find({ name: child_birth_date }).exists()).toBeFalsy();
  });

  describe("when child birth or placement date is in the future", () => {
    let spy;

    beforeAll(() => {
      spy = jest.spyOn(DateTime, "local").mockImplementation(() => {
        return {
          toISODate: () => now,
        };
      });
    });

    afterAll(() => {
      spy.mockRestore();
    });

    it("sets has_future_child_date as true for future birth bonding leave when claim is already populated", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingBirthLeaveReason(future)
        .create();
      const { appLogic, submitForm } = setup(claim);

      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        expect.any(String),
        {
          leave_details: {
            child_birth_date: future,
            child_placement_date: null,
            has_future_child_date: true,
          },
        }
      );
    });

    it("sets has_future_child_date as true for future birth bonding leave when data is manually populated", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingLeaveReason()
        .create();
      claim.leave_details.reason_qualifier = ReasonQualifier.newBorn;

      const { appLogic, changeField, submitForm } = setup(claim);

      changeField("leave_details.child_birth_date", future);

      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        expect.any(String),
        {
          leave_details: {
            child_birth_date: future,
            child_placement_date: null,
            has_future_child_date: true,
          },
        }
      );
    });

    it("sets has_future_child_date as true for future placement bonding leave when claim is already populated", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingFosterCareLeaveReason(future)
        .create();
      const { appLogic, submitForm } = setup(claim);

      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        expect.any(String),
        {
          leave_details: {
            child_birth_date: null,
            child_placement_date: future,
            has_future_child_date: true,
          },
        }
      );
    });

    it("sets has_future_child_date as true for future placement bonding leave when data is manually populated", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingLeaveReason()
        .create();
      claim.leave_details.reason_qualifier = ReasonQualifier.fosterCare;

      const { appLogic, changeField, submitForm } = setup(claim);
      changeField("leave_details.child_placement_date", future);
      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        expect.any(String),
        {
          leave_details: {
            child_birth_date: null,
            child_placement_date: future,
            has_future_child_date: true,
          },
        }
      );
    });
  });

  describe("when child birth or placement date is in the past", () => {
    let spy;

    beforeAll(() => {
      spy = jest.spyOn(DateTime, "local").mockImplementation(() => {
        return {
          toISODate: () => now,
        };
      });
    });

    afterAll(() => {
      spy.mockRestore();
    });

    it("sets has_future_child_date as false for past birth bonding leave when claim is pre-populated", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingBirthLeaveReason(past)
        .create();
      const { appLogic, submitForm } = setup(claim);

      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        expect.any(String),
        {
          leave_details: {
            child_birth_date: past,
            child_placement_date: null,
            has_future_child_date: false,
          },
        }
      );
    });

    it("sets has_future_child_date as false for past birth bonding leave when data is manually populated", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingLeaveReason()
        .create();
      claim.leave_details.reason_qualifier = ReasonQualifier.newBorn;

      const { appLogic, changeField, submitForm } = setup(claim);
      changeField("leave_details.child_birth_date", past);
      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        expect.any(String),
        {
          leave_details: {
            child_birth_date: past,
            child_placement_date: null,
            has_future_child_date: false,
          },
        }
      );
    });

    it("sets has_future_child_date as false for past placement bonding leave when claim is pre-populated", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingFosterCareLeaveReason(past)
        .create();
      const { appLogic, submitForm } = setup(claim);
      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        expect.any(String),
        {
          leave_details: {
            child_birth_date: null,
            child_placement_date: past,
            has_future_child_date: false,
          },
        }
      );
    });

    it("sets has_future_child_date as false for past placement bonding leave when data is manually populated", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .bondingLeaveReason()
        .create();
      claim.leave_details.reason_qualifier = ReasonQualifier.fosterCare;

      const { appLogic, changeField, submitForm } = setup(claim);
      changeField("leave_details.child_placement_date", past);
      await submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        expect.any(String),
        {
          leave_details: {
            child_birth_date: null,
            child_placement_date: past,
            has_future_child_date: false,
          },
        }
      );
    });
  });
});
