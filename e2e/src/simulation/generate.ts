import { PortalApplicationSubmission } from "./types";
import faker from "faker";

/**
 * This function is responsible for generating a dummy claim.
 *
 * It will eventually be customizable so different scenarios can
 * use it differently.
 */
export default function generate(): PortalApplicationSubmission {
  const endDate = soon(faker.random.number(365));
  const startDate = faker.date.between(new Date(), endDate);
  const notificationDate = faker.date.recent(60);

  const app: PortalApplicationSubmission = {
    date_of_birth: fmt(faker.date.past(80)),
    employment_status: "Employed",
    first_name: faker.name.firstName(),
    last_name: faker.name.lastName(),
    leave_details: {
      continuous_leave_periods: [
        {
          start_date: fmt(startDate),
          end_date: fmt(endDate),
          is_estimated: true,
        },
      ],
      employer_notification_date: fmt(notificationDate),
      employer_notified: true,
      intermittent_leave_periods: [],
      reason: "Serious Health Condition - Employee",
      reduced_schedule_leave_periods: [],
    },
    payment_preferences: [],
    status: "Started",
    tax_identifier_last4: faker.phone.phoneNumber("####"),
  };
  return app;
}

// Replacement for faker.date.soon(), which is slated to be released in the future.
function soon(days: number, refDate?: string): Date {
  let date = new Date();
  if (typeof refDate !== "undefined") {
    date = new Date(Date.parse(refDate));
  }

  const range = {
    min: 1000,
    max: (days || 1) * 24 * 3600 * 1000,
  };

  let future = date.getTime();
  future += faker.random.number(range); // some time from now to N days later, in milliseconds
  date.setTime(future);

  return date;
}

function fmt(date: Date): string {
  return `${date.getFullYear()}-${(date.getMonth() + 1)
    .toString()
    .padStart(2, "0")}-${date.getDate().toString().padStart(2, "0")}`;
}
