import assert from "assert";
import { isNil } from "lodash";
/**
 * Split provided minutes across a 7 day week
 * @param {number} minutesWorkedPerWeek - average minutes worked per week. Must be an integer.
 * @returns {number[]} dailyMinutes
 */
function spreadMinutesOverWeek(minutesWorkedPerWeek) {
  assert(!isNil(minutesWorkedPerWeek));
  const remainder = minutesWorkedPerWeek % 7;
  const dailyMinutes = [];

  for (let i = 0; i < 7; i++) {
    if (i < remainder) {
      dailyMinutes.push(Math.ceil(minutesWorkedPerWeek / 7));
    } else {
      dailyMinutes.push(Math.floor(minutesWorkedPerWeek / 7));
    }
  }

  return dailyMinutes;
}

export default spreadMinutesOverWeek;
