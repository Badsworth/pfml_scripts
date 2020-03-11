import i18next from "i18next";

const quarterMap = {
  Q1: i18next.t("components.wagesTable.q1MonthRange"),
  Q2: i18next.t("components.wagesTable.q2MonthRange"),
  Q3: i18next.t("components.wagesTable.q3MonthRange"),
  Q4: i18next.t("components.wagesTable.q4MonthRange"),
};

/**
 * convert period_id from /wages endpoint to months.
 * @param {string} periodId - periodId returned from wages input in format Q1YYYY
 * @returns {string}`${startMonth} - ${endMonth} ${year}`
 */
const convertPeriodToMonths = periodId => {
  const format = /Q[1-4]2\d\d\d/;
  const correctFormat = periodId.match(format) !== null;

  if (!correctFormat) {
    return null;
  }

  const quarter = periodId.substring(0, 2);
  const year =
    quarter === "Q1" ? +periodId.substring(2, 6) - 1 : periodId.substring(2, 6);

  return `${quarterMap[quarter]} ${year}`;
};

export default convertPeriodToMonths;
