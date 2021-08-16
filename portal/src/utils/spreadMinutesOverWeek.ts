import assert from "assert";
import { isNil } from "lodash";
/**
 * Split provided minutes across a 7 day week
 * @param {number} minutesWorkedPerWeek - average minutes worked per week. Must be an integer.
 * @returns {number[]} dailyMinutes
 */
function spreadMinutesOverWeek(minutesWorkedPerWeek) {
  assert(!isNil(minutesWorkedPerWeek));
  const dailyMinutes = [];
  const incrementMinutes = 15;

  // API-1611 - minimum of 15-minute increments for the smallest split so we can't just divide evenly by 7 days
  const incrementsPerDay = minutesWorkedPerWeek / incrementMinutes / 7;
  const remainderIncrements = (minutesWorkedPerWeek / incrementMinutes) % 7;
  const remainderMinutes = minutesWorkedPerWeek % incrementMinutes;

  for (let i = 0; i < 7; i++) {
    if (
      remainderMinutes ||
      (remainderIncrements && i < Math.floor(remainderIncrements))
    ) {
      const extraFullIncrementMinutes =
        i < Math.floor(remainderIncrements) ? 15 : 0;
      const extraPartialIncrementMinutes =
        i === Math.ceil(remainderIncrements) - 1 ? remainderMinutes : 0;
      dailyMinutes.push(
        Math.floor(incrementsPerDay) * incrementMinutes + // even distribution
          extraFullIncrementMinutes + // extra 15-minute increments
          extraPartialIncrementMinutes // leftover minutes
      );
    } else {
      dailyMinutes.push(Math.floor(incrementsPerDay) * incrementMinutes);
    }
  }

  return dailyMinutes;
}

export default spreadMinutesOverWeek;
