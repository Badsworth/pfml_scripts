import { PaymentDetail } from "../../src/models/ClaimDetail";
import dayjs from "dayjs";
import faker from "faker";
import formatDate from "../../src/utils/formatDate";
import { uniqueId } from "lodash";

/**
 * Creates mock payments for tests and stories.
 * @param {object} customDetails - Custom payment details to include.
 * @param {boolean} [isConstant=false] - When true, constant data is used.
 * @returns {object}
 *
 * @example
 * createMockPayment()
 * createMockPayment({ payment_method: "Check", status: "Pending" })
 * createMockPayment({ status: "Pending" }, true)
 */
type PaymentStatus = "Cancelled" | "Delayed" | "Pending" | "Sent to bank";

// Creates random number up to limit {number} value
interface GetRandomIntegerProps {
  length?: number;
  limit: number;
  isString?: boolean;
}

const getRandomInteger = ({
  length = 2,
  limit,
  isString = false,
}: GetRandomIntegerProps) => {
  const randomNumber = Math.floor(Math.random() * limit);

  return isString ? `0${randomNumber + 1}`.slice(-length) : randomNumber;
};

// Define these here, rather than in the exported function so that they don't change
// every time you change a storybook control.
// Random date
const randomMonth = getRandomInteger({ limit: 12, isString: true });
const randomDay = getRandomInteger({ limit: 28, isString: true });
const randomStartDate = `${new Date().getFullYear()}-${randomMonth}-${randomDay}`;
// Random dollar amount
const randomAmount = Number(getRandomInteger({ limit: 500, length: 3 }));

export const createMockPayment = (
  customDetails: Partial<PaymentDetail>,
  isConstant = false,
  startDate = randomStartDate,
  amount = randomAmount
): PaymentDetail => {
  // To use constant data (helps w/snapshots & similar)
  if (isConstant) {
    return {
      payment_id: uniqueId("1234"),
      period_start_date: "2021-11-08",
      period_end_date: "2021-11-15",
      amount: 100,
      sent_to_bank_date: "2021-11-15",
      payment_method: "Check",
      expected_send_date_start: "2021-11-15",
      expected_send_date_end: "2021-11-21",
      status: "Pending",
      ...customDetails,
    };
  }

  // Helper method to generate future dates
  const getFutureDate = (originalDate: string, skipDayCount: number) => {
    return formatDate(dayjs(originalDate).add(skipDayCount, "day").format())
      .short()
      .replace(/\//g, "-");
  };

  // Payment date configuration
  const endDate = getFutureDate(startDate, 6);
  const sendDate = endDate;
  const sendDateEnd = getFutureDate(sendDate, 3);

  return {
    payment_id: uniqueId("1234"),
    period_start_date: startDate,
    period_end_date: endDate,
    amount,
    sent_to_bank_date: endDate,
    payment_method: faker.random.arrayElement<string>([
      "Check",
      "Elec Funds Transfer",
    ]),
    expected_send_date_start: sendDate,
    expected_send_date_end: sendDateEnd,
    status: faker.random.arrayElement<PaymentStatus>([
      "Cancelled",
      "Delayed",
      "Pending",
      "Sent to bank",
    ]),
    ...customDetails,
  };
};
