import {
  DurationBasis,
  FrequencyIntervalBasis,
  IntermittentLeavePeriod,
} from "../models/BenefitsApplication";
import findKeyByValue from "./findKeyByValue";

/**
 * Get an i18n `context` string for outputting a plain language description
 * of an Intermittent Leave Period's frequency and duration data
 */
function getI18nContextForIntermittentFrequencyDuration(
  leavePeriod: IntermittentLeavePeriod
) {
  let frequencyContext;
  const durationContext = findKeyByValue(
    DurationBasis,
    leavePeriod.duration_basis
  );

  if (
    leavePeriod.frequency_interval_basis === FrequencyIntervalBasis.months &&
    leavePeriod.frequency === 6
  ) {
    frequencyContext = "irregularMonths";
  } else {
    frequencyContext = findKeyByValue(
      FrequencyIntervalBasis,
      leavePeriod.frequency_interval_basis
    );
  }

  // For example: months_hours or weeks_days
  return `${frequencyContext}_${durationContext}`;
}

export default getI18nContextForIntermittentFrequencyDuration;
