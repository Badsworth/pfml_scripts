import {
  DurationBasis,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
} from "../../src/models/BenefitsApplication";
import getI18nContextForIntermittentFrequencyDuration from "../../src/utils/getI18nContextForIntermittentFrequencyDuration";

describe("getI18nContextForIntermittentFrequencyDuration", () => {
  it("combines frequency_interval_basis with duration_basis", () => {
    const leavePeriod = new IntermittentLeavePeriod({
      duration_basis: DurationBasis.hours,
      frequency_interval_basis: FrequencyIntervalBasis.months,
    });

    const context = getI18nContextForIntermittentFrequencyDuration(leavePeriod);

    expect(context).toBe("months_hours");
  });

  it("outputs the irregular over 6 months when frequency is set to 6", () => {
    const leavePeriod = new IntermittentLeavePeriod({
      duration_basis: DurationBasis.days,
      frequency_interval_basis: FrequencyIntervalBasis.months,
      frequency: 6,
    });

    const context = getI18nContextForIntermittentFrequencyDuration(leavePeriod);

    expect(context).toBe("irregularMonths_days");
  });
});
