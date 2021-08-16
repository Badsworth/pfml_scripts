import {
  DurationBasis,
  FrequencyIntervalBasis,
} from "../models/BenefitsApplication";
import findKeyByValue from "./findKeyByValue";

/** @typedef {import('../models/BenefitsApplication').IntermittentLeavePeriod} IntermittentLeavePeriod */

/**
 * Get an i18n `context` string for outputting a plain language description
 * of an Intermittent Leave Period's frequency and duration data
 * @param {IntermittentLeavePeriod} leavePeriod
 * @returns {string}
 */
function getI18nContextForIntermittentFrequencyDuration(leavePeriod) {
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
