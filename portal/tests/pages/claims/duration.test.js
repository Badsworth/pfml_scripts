import {
  ContinuousLeavePeriod,
  DurationBasis,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
  ReducedScheduleLeavePeriod,
} from "../../../src/models/Claim";
import Duration, { every6monthsId } from "../../../src/pages/claims/duration";
import { act } from "react-dom/test-utils";
import { random } from "lodash";
import { renderWithAppLogic } from "../../test-utils";

describe("Duration", () => {
  describe("regardless of duration type", () => {
    it("initially renders the page without conditional fields", () => {
      const { wrapper } = renderWithAppLogic(Duration);

      expect(wrapper).toMatchSnapshot();
      expect(
        wrapper.find({ name: "continuous_section" }).prop("visible")
      ).toBeFalsy();
      expect(
        wrapper.find({ name: "reduced_schedule_section" }).prop("visible")
      ).toBeFalsy();
      expect(
        wrapper.find({ name: "intermittent_section" }).prop("visible")
      ).toBeFalsy();
    });
  });

  describe("when claim has a continous leave entry", () => {
    const claimAttrs = {
      temp: {
        leave_details: {
          continuous_leave_periods: [new ContinuousLeavePeriod()],
        },
      },
    };

    it("it renders continuous leave section", () => {
      const { wrapper } = renderWithAppLogic(Duration, { claimAttrs });
      expect(wrapper.find({ name: "continuous_section" }).prop("visible")).toBe(
        true
      );
    });
  });

  describe("when claim has a reduced schedule entry", () => {
    const claimAttrs = {
      temp: {
        leave_details: {
          reduced_schedule_leave_periods: [new ReducedScheduleLeavePeriod()],
        },
      },
    };

    it("it renders reduced schedule leave section", () => {
      const { wrapper } = renderWithAppLogic(Duration, { claimAttrs });
      expect(
        wrapper.find({ name: "reduced_schedule_section" }).prop("visible")
      ).toBe(true);
    });
  });

  describe("when claim has an intermittent leave entry", () => {
    const claimAttrs = {
      leave_details: {
        intermittent_leave_periods: [new IntermittentLeavePeriod()],
      },
    };

    it("it renders intermittent leave section", () => {
      const { wrapper } = renderWithAppLogic(Duration, { claimAttrs });
      expect(
        wrapper.find({ name: "intermittent_section" }).prop("visible")
      ).toBe(true);
    });
  });

  describe("when user clicks continue", () => {
    it("calls claims.update", () => {
      const claimAttrs = {
        leave_details: {
          intermittent_leave_periods: [new IntermittentLeavePeriod()],
        },
        temp: {
          leave_details: {
            continuous_leave_periods: [new ContinuousLeavePeriod()],
            reduced_schedule_leave_periods: [new ReducedScheduleLeavePeriod()],
          },
        },
      };

      const { wrapper, appLogic, claim } = renderWithAppLogic(Duration, {
        claimAttrs,
      });
      const updateClaimSpy = jest.spyOn(appLogic.claims, "update");

      act(() => {
        wrapper.find("QuestionPage").simulate("save");
      });

      expect(updateClaimSpy).toHaveBeenCalledWith(
        claim.application_id,
        expect.objectContaining(claimAttrs)
      );
    });
  });

  describe("intermittent leave section", () => {
    const intermittentClaimAttrs = (attrs) => ({
      leave_details: {
        intermittent_leave_periods: [new IntermittentLeavePeriod(attrs)],
      },
    });
    const frequencyBasisInputName =
      "leave_details.intermittent_leave_periods[0].frequency_interval_basis";
    const frequencyInputName =
      "leave_details.intermittent_leave_periods[0].frequency";
    const durationBasisInputName =
      "leave_details.intermittent_leave_periods[0].duration_basis";
    const durationInputName =
      "leave_details.intermittent_leave_periods[0].duration";

    describe("when claim has an intermittent leave frequency_interval_basis", () => {
      const claimAttrs = intermittentClaimAttrs({
        frequency_interval: null,
        frequency_interval_basis: Object.values(FrequencyIntervalBasis)[
          random(0, 2)
        ],
      });

      it("it renders frequency question", () => {
        const { wrapper } = renderWithAppLogic(Duration, { claimAttrs });
        expect(
          wrapper.find({ name: "frequency_question" }).prop("visible")
        ).toBe(true);
      });
    });

    describe("when claim has an intermittent leave duration_basis", () => {
      const claimAttrs = intermittentClaimAttrs({
        duration: null,
        duration_basis: Object.values(DurationBasis)[random(0, 1)],
      });

      it("it renders duration question", () => {
        const { wrapper } = renderWithAppLogic(Duration, { claimAttrs });
        expect(
          wrapper.find({ name: "duration_question" }).prop("visible")
        ).toBe(true);
      });
    });

    describe("when frequency_interval_basis is in weeks", () => {
      let wrapper;
      const claimAttrs = intermittentClaimAttrs({
        frequency_interval: null,
        frequency_interval_basis: FrequencyIntervalBasis.weeks,
      });

      beforeEach(() => {
        ({ wrapper } = renderWithAppLogic(Duration, { claimAttrs }));
      });

      it("the per_week radio is selected", () => {
        const choices = wrapper
          .find({ name: frequencyBasisInputName })
          .prop("choices");
        choices.forEach((choice) => {
          if (choice.key === "per_week") {
            expect(choice.checked).toBe(true);
          } else {
            expect(choice.checked).toBe(false);
          }
        });
      });

      it("shows appropriate frequency label", () => {
        expect(
          wrapper.find({ name: frequencyInputName }).prop("label")
        ).toMatchInlineSnapshot(`"Estimate how many absences per week."`);
      });
    });

    describe("when frequency_interval_basis is months with no frequency_interval", () => {
      let wrapper;
      const claimAttrs = intermittentClaimAttrs({
        frequency_interval: null,
        frequency_interval_basis: FrequencyIntervalBasis.months,
      });

      beforeEach(() => {
        ({ wrapper } = renderWithAppLogic(Duration, { claimAttrs }));
      });

      it("the per_months radio is selected", () => {
        const choices = wrapper
          .find({ name: frequencyBasisInputName })
          .prop("choices");
        choices.forEach((choice) => {
          if (choice.key === "per_month") {
            expect(choice.checked).toBe(true);
          } else {
            expect(choice.checked).toBe(false);
          }
        });
      });

      it("shows appropriate frequency label", () => {
        expect(
          wrapper.find({ name: frequencyInputName }).prop("label")
        ).toMatchInlineSnapshot(`"Estimate how many absences per month."`);
      });
    });

    describe("when frequency_interval_basis is months and frequency interval is 6", () => {
      let wrapper;
      const claimAttrs = intermittentClaimAttrs({
        frequency_interval: 6,
        frequency_interval_basis: FrequencyIntervalBasis.months,
      });

      beforeEach(() => {
        ({ wrapper } = renderWithAppLogic(Duration, { claimAttrs }));
      });

      it("the every 6 months radio is selected", () => {
        const choices = wrapper
          .find({ name: frequencyBasisInputName })
          .prop("choices");
        choices.forEach((choice) => {
          if (choice.key === every6monthsId) {
            expect(choice.checked).toBe(true);
          } else {
            expect(choice.checked).toBe(false);
          }
        });
      });

      it("shows appropriate frequency label", () => {
        expect(
          wrapper.find({ name: frequencyInputName }).prop("label")
        ).toMatchInlineSnapshot(
          `"Estimate how many absences over the next 6 months."`
        );
      });
    });

    describe("when duration_basis is days", () => {
      let wrapper;
      const claimAttrs = intermittentClaimAttrs({
        duration: null,
        duration_basis: DurationBasis.days,
      });

      beforeEach(() => {
        ({ wrapper } = renderWithAppLogic(Duration, { claimAttrs }));
      });

      it("the days radio is selected", () => {
        const choices = wrapper
          .find({ name: durationBasisInputName })
          .prop("choices");
        choices.forEach((choice) => {
          if (choice.key === "days") {
            expect(choice.checked).toBe(true);
          } else {
            expect(choice.checked).toBe(false);
          }
        });
      });

      it("shows appropriate duration label", () => {
        expect(
          wrapper.find({ name: durationInputName }).prop("label")
        ).toMatchInlineSnapshot(
          `"How many days of work will you miss per absence?"`
        );
      });
    });

    describe("when duration_basis is hours", () => {
      let wrapper;
      const claimAttrs = intermittentClaimAttrs({
        duration: null,
        duration_basis: DurationBasis.hours,
      });

      beforeEach(() => {
        ({ wrapper } = renderWithAppLogic(Duration, { claimAttrs }));
      });

      it("the hours radio is selected", () => {
        const choices = wrapper
          .find({ name: durationBasisInputName })
          .prop("choices");
        choices.forEach((choice) => {
          if (choice.key === "hours") {
            expect(choice.checked).toBe(true);
          } else {
            expect(choice.checked).toBe(false);
          }
        });
      });

      it("shows appropriate duration label", () => {
        expect(
          wrapper.find({ name: durationInputName }).prop("label")
        ).toMatchInlineSnapshot(
          `"How many hours of work will you miss per absence?"`
        );
      });
    });

    describe("user interaction", () => {
      let wrapper;
      const claimAttrs = intermittentClaimAttrs();
      beforeEach(() => {
        ({ wrapper } = renderWithAppLogic(Duration, {
          claimAttrs,
        }));
      });

      describe("when user clicks per_week frequency basis", () => {
        it("selects per_week radio", () => {
          act(() => {
            wrapper.find({ name: frequencyBasisInputName }).simulate("change", {
              preventDefault: jest.fn(),
              target: {
                id: "InputChoiceX",
                name: frequencyBasisInputName,
                value: FrequencyIntervalBasis.weeks,
              },
            });
          });

          const choices = wrapper
            .find({ name: frequencyBasisInputName })
            .prop("choices");
          expect(choices[0].checked).toBe(true);
        });
      });

      describe("when user clicks per_month frequency basis", () => {
        it("selects per_month radio", () => {
          act(() => {
            wrapper.find({ name: frequencyBasisInputName }).simulate("change", {
              preventDefault: jest.fn(),
              target: {
                id: "InputChoiceX",
                name: frequencyBasisInputName,
                value: FrequencyIntervalBasis.months,
              },
            });
          });

          const choices = wrapper
            .find({ name: frequencyBasisInputName })
            .prop("choices");
          expect(choices[1].checked).toBe(true);
        });
      });

      describe("when user clicks every6months frequency basis", () => {
        it("selects every6months radio", () => {
          act(() => {
            wrapper.find({ name: frequencyBasisInputName }).simulate("change", {
              preventDefault: jest.fn(),
              target: {
                id: every6monthsId,
                name: frequencyBasisInputName,
                value: FrequencyIntervalBasis.months,
              },
            });
          });

          const choices = wrapper
            .find({ name: frequencyBasisInputName })
            .prop("choices");
          expect(choices[2].checked).toBe(true);
        });
      });
    });
  });
});
