import { groupBy, map, sumBy, uniqBy } from "lodash";

const formatDollar = new Intl.NumberFormat("en-US", {
  style: "currency",
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
  currency: "USD"
}).format;

/**
 * Summarize wage data for review by employee
 * @param {{ employer_id: string, employer_qtr_id: number }[]} wages - Wages object returned by /wages API endpoint.
 * @returns {{ totalEmployers: number, earningsByEmployer: [ { employer: string, earnings: string } ] }}
 */
const summarizeWages = wages => ({
  totalEmployers: uniqBy(wages, "employer_id").length,
  // _.map allows us to loop through a js object and
  // return an array that contains an object for each key/value pair
  earningsByEmployer: map(
    // create an object that groups wages by employer_id
    // { "employer-1-id": [...employerWages], "employer-2-id": [...employerWages] }
    groupBy(wages, "employer_id"),
    // for each key/value pair in object above
    // sum employer_qtr_wages and format as USD
    (employerWages, employerId) => ({
      employer: employerId,
      earnings: formatDollar(
        sumBy(employerWages, "employer_qtr_wages").toFixed()
      )
    })
  )
});

export default summarizeWages;
