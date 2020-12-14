import EmployerBenefit from "../models/EmployerBenefit";
import _ from "lodash";

/**
 * Returns an updated array (for employer benefits or previous leaves) with amended data
 *
 * @param {Array} amendments
 * @param {object} updatedValue
 * @returns {Array}
 */
const updateAmendment = (amendments, updatedValue) => {
  return amendments.map((amendment) => {
    const idKey =
      amendment instanceof EmployerBenefit
        ? "employer_benefit_id"
        : "previous_leave_id";
    const amendmentId = _.get(amendment, idKey);
    const updatedValueId = _.get(updatedValue, idKey);

    if (amendmentId === updatedValueId) {
      return _.merge(_.clone(amendment), updatedValue);
    }

    return amendment;
  });
};

export default updateAmendment;
