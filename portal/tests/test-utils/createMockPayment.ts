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

interface CreateMockPaymentProps {
  payment_id?: string;
  period_start_date?: string;
  period_end_date?: string;
  amount?: number | null;
  sent_to_bank_date?: string | null;
  payment_method?: string;
  expected_send_date_start?: string | null;
  expected_send_date_end?: string | null;
  status?: PaymentStatus;
}

export const createMockPayment = (
  customDetails: CreateMockPaymentProps,
  isConstant = false
) => {
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

  // Random month/day for notice date
  const randomMonth = getRandomInteger({ limit: 12, isString: true });
  const randomDay = getRandomInteger({ limit: 28, isString: true });

  // Helper method to generate future dates
  const getFutureDate = (originalDate: string, skipDayCount: number) => {
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
    payment_id: uniqueId("1234"),
    period_start_date: startDate,
    period_end_date: endDate,
    amount: getRandomInteger({ limit: 500, length: 3 }),
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
