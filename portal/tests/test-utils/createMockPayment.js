import dayjs from "dayjs";
import formatDate from "../../src/utils/formatDate";
import { uniqueId } from "lodash";

/**
 * Creates mock payments for tests and stories.s
 * @param {string} paymentStatus - Status of payment.
 * @param {string} paymentMethod - Method used to pay claimant.
 * @param {boolean} [isConstant=false] - When true, constant data is used.
 * @returns {object}
 *
 * @example
 * createMockPayment("Pending", "Check")
 * createMockPayment("Pending", "Check", true)
 */
export const createMockPayment = (
  paymentStatus,
  paymentMethod,
  isConstant = false
) => {
  // Creates random number up to limit {number} value
  const getRandomInteger = (limit, length = 2) => {
    const randomNumber = Math.floor(Math.random() * limit) + 1;
    return `0${randomNumber}`.slice(-length);
  };

  // To use constant data (helps w/snapshots & similar)
  if (isConstant) {
    return {
      payment_id: uniqueId(getRandomInteger(9999, 4)),
      period_start_date: "2021-11-08",
      period_end_date: "2021-11-15",
      amount: 100,
      sent_to_bank_date: "2021-11-15",
      payment_method: paymentMethod,
      expected_send_date_start: "2021-11-15",
      expected_send_date_end: "2021-11-21",
      status: paymentStatus,
    };
  }

  // Random month/day for notice date
  const randomMonth = getRandomInteger(12);
  const randomDay = getRandomInteger(28);

  // Helper method to generate future dates
  const getFutureDate = (originalDate, skipDayCount) => {
    return formatDate(dayjs(originalDate).add(skipDayCount, "day").format())
      .short()
      .replace(/\//g, "-");
  };

  // Payment date configuration
  const startDate = `${new Date().getFullYear()}-${randomMonth}-${randomDay}`;
  const endDate = getFutureDate(startDate, 6);
  const sendDate = endDate;
  const sendDateEnd = getFutureDate(sendDate, 3);

  return {
    payment_id: uniqueId(getRandomInteger(9999, 4)),
    period_start_date: startDate,
    period_end_date: endDate,
    amount: getRandomInteger(500, 3),
    sent_to_bank_date: endDate,
    payment_method: paymentMethod,
    expected_send_date_start: sendDate,
    expected_send_date_end: sendDateEnd,
    status: paymentStatus,
  };
};
