import {
  DurationBasis,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
} from "../../../src/models/BenefitsApplication";
import IntermittentFrequency, {
  irregularOver6MonthsId,
} from "../../../src/pages/applications/intermittent-frequency";
import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";

jest.mock("../../../src/hooks/useAppLogic");

const frequencyBasisInputName =
  "leave_details.intermittent_leave_periods[0].frequency_interval_basis";

describe("IntermittentFrequency", () => {
  const intermittentClaimAttrs = (attrs) => ({
    leave_details: {
      intermittent_leave_periods: [new IntermittentLeavePeriod({ ...attrs })],
    },
  });

  it("renders the page", () => {
    const { wrapper } = renderWithAppLogic(IntermittentFrequency, {
      claimAttrs: new MockClaimBuilder().intermittent().create(),
    });

    expect(wrapper).toMatchSnapshot();
  });

  it("it displays frequency and duration_basis questions when a frequency_interval_basis is selected", () => {
    const { wrapper: blankClaimWrapper } = renderWithAppLogic(
      IntermittentFrequency
    );
    const { wrapper: wrapperWithState } = renderWithAppLogic(
      IntermittentFrequency,
      {
        claimAttrs: intermittentClaimAttrs({
          frequency_interval_basis: FrequencyIntervalBasis.months,
        }),
      }
    );

    expect(
      blankClaimWrapper.find("ConditionalContent").at(0).prop("visible")
    ).toBe(false);
    expect(
      wrapperWithState.find("ConditionalContent").at(0).prop("visible")
    ).toBe(true);
  });

  it("it displays duration question when a duration_basis is selected", () => {
    const { wrapper: blankClaimWrapper } = renderWithAppLogic(
      IntermittentFrequency
    );
    const { wrapper: wrapperWithState } = renderWithAppLogic(
      IntermittentFrequency,
      {
        claimAttrs: intermittentClaimAttrs({
          duration_basis: DurationBasis.days,
        }),
      }
    );

    expect(
      blankClaimWrapper
        .find({ name: "leave_details.intermittent_leave_periods[0].duration" })
        .exists()
    ).toBe(false);
    expect(
      wrapperWithState
        .find({ name: "leave_details.intermittent_leave_periods[0].duration" })
        .exists()
    ).toBe(true);
  });

  it("displays frequency label corresponding to selected frequency interval and basis", () => {
    expect.assertions();

    const options = [
      {
        frequency_interval_basis: FrequencyIntervalBasis.weeks,
      },
      {
        frequency_interval_basis: FrequencyIntervalBasis.months,
      },
      {
        frequency_interval: 6,
        frequency_interval_basis: FrequencyIntervalBasis.months,
      },
    ];

    options.forEach((option) => {
      const { wrapper } = renderWithAppLogic(IntermittentFrequency, {
        claimAttrs: intermittentClaimAttrs(option),
      });

      expect(
        wrapper
          .find({
            name: "leave_details.intermittent_leave_periods[0].frequency",
          })
          .prop("label")
      ).toMatchSnapshot();
    });
  });

  it("displays duration label corresponding to selected duration basis", () => {
    expect.assertions();

    const options = [
      {
        duration_basis: DurationBasis.days,
      },
      {
        duration_basis: DurationBasis.hours,
      },
    ];

    options.forEach((option) => {
      const { wrapper } = renderWithAppLogic(IntermittentFrequency, {
        claimAttrs: intermittentClaimAttrs(option),
      });

      expect(
        wrapper
          .find({
            name: "leave_details.intermittent_leave_periods[0].duration",
          })
          .prop("label")
      ).toMatchSnapshot();
    });
  });

  it("displays Alert about having medical form when claim is for Medical leave", () => {
    const { wrapper: medicalWrapper } = renderWithAppLogic(
      IntermittentFrequency,
      {
        claimAttrs: new MockClaimBuilder().medicalLeaveReason().create(),
      }
    );
    const { wrapper: bondingWrapper } = renderWithAppLogic(
      IntermittentFrequency,
      {
        claimAttrs: new MockClaimBuilder().bondingBirthLeaveReason().create(),
      }
    );
    const alert = medicalWrapper.find("Alert");

    expect(alert.exists()).toBe(true);
    expect(alert).toMatchSnapshot();
    expect(bondingWrapper.find("Alert").exists()).toBe(false);
  });

  it("displays hint text with medical form context when claim is for Medical leave", () => {
    expect.assertions();

    const { wrapper: medicalWrapper } = renderWithAppLogic(
      IntermittentFrequency,
      {
        claimAttrs: new MockClaimBuilder()
          .medicalLeaveReason()
          .intermittent()
          .create(),
      }
    );
    const { wrapper: bondingWrapper } = renderWithAppLogic(
      IntermittentFrequency,
      {
        claimAttrs: new MockClaimBuilder()
          .bondingBirthLeaveReason()
          .intermittent()
          .create(),
      }
    );

    const fieldFinder = (nodeWrapper) =>
      ["InputNumber", "InputChoiceGroup"].includes(nodeWrapper.name());
    const medicalWrapperFields = medicalWrapper.findWhere(fieldFinder);
    const bondingWrapperFields = bondingWrapper.findWhere(fieldFinder);

    medicalWrapperFields.forEach((field) => {
      expect(field.prop("hint")).toMatchSnapshot();
    });

    bondingWrapperFields.forEach((field) => {
      expect(field.prop("hint")).toBeNull();
    });
  });

  describe("frequency_basis change handler", () => {
    let changeRadioGroup, wrapper;
    const claimAttrs = intermittentClaimAttrs();

    beforeEach(() => {
      ({ wrapper } = renderWithAppLogic(IntermittentFrequency, {
        claimAttrs,
      }));
      ({ changeRadioGroup } = simulateEvents(wrapper));
    });

    it("selects Months radio", () => {
      changeRadioGroup(frequencyBasisInputName, FrequencyIntervalBasis.months);

      const choices = wrapper
        .find({ name: frequencyBasisInputName })
        .prop("choices");

      expect(choices[1].checked).toBe(true);
    });

    it("selects 'Irregular over 6 months' radio when input ID matches", () => {
      changeRadioGroup(
        frequencyBasisInputName,
        FrequencyIntervalBasis.months,
        irregularOver6MonthsId
      );

      const choices = wrapper
        .find({ name: frequencyBasisInputName })
        .prop("choices");

      expect(choices[2].checked).toBe(true);
    });
  });

  it("sends the page's fields and the leave period ID to the API when the data is already on the claim", () => {
    const claim = new MockClaimBuilder().intermittent().create();
    const {
      duration,
      duration_basis,
      frequency,
      frequency_interval,
      frequency_interval_basis,
      leave_period_id,
    } = claim.leave_details.intermittent_leave_periods[0];

    const { appLogic, wrapper } = renderWithAppLogic(IntermittentFrequency, {
      claimAttrs: claim,
    });

    wrapper.find("QuestionPage").simulate("save");

    expect(appLogic.claims.update).toHaveBeenCalledWith(claim.application_id, {
      leave_details: {
        intermittent_leave_periods: [
          {
            duration,
            duration_basis,
            frequency,
            frequency_interval,
            frequency_interval_basis,
            leave_period_id,
          },
        ],
      },
    });
  });

  it("sends the page's fields and the leave period ID to the API when the data is newly entered", async () => {
    const claim = new MockClaimBuilder().intermittent().create();

    const frequency_interval_basis = FrequencyIntervalBasis.months;
    const frequency = 6;
    const frequency_interval = 6;
    const duration_basis = DurationBasis.hours;
    const duration = 6;

    const { appLogic, wrapper } = renderWithAppLogic(IntermittentFrequency, {
      claimAttrs: claim,
    });

    const { changeField, changeRadioGroup, submitForm } = simulateEvents(
      wrapper
    );

    changeRadioGroup(
      frequencyBasisInputName,
      frequency_interval_basis,
      irregularOver6MonthsId
    );
    changeField(
      "leave_details.intermittent_leave_periods[0].frequency",
      frequency
    );
    changeRadioGroup(
      "leave_details.intermittent_leave_periods[0].duration_basis",
      duration_basis
    );
    changeField(
      "leave_details.intermittent_leave_periods[0].duration",
      duration
    );

    await submitForm();

    expect(appLogic.claims.update).toHaveBeenCalledWith(claim.application_id, {
      leave_details: {
        intermittent_leave_periods: [
          {
            duration,
            duration_basis,
            frequency,
            frequency_interval,
            frequency_interval_basis,
            leave_period_id: "mock-leave-period-id",
          },
        ],
      },
    });
  });
});
