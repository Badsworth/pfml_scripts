import { clone, get, merge } from "lodash";
import EmployerBenefit from "../models/EmployerBenefit";
import PreviousLeave from "../models/PreviousLeave";

/**
 * Returns an updated array (for employer benefits or previous leaves) with amended data
 *
 * @param {Array} amendments
 * @param {object} updatedValue
 * @returns {Array}
 */
const updateAmendment = (amendments, updatedValue) => {
  return amendments.map((amendment) => {
    const idKey = getIdKey(amendment);

    if (idKey) {
      const amendmentId = get(amendment, idKey);
      const updatedValueId = get(updatedValue, idKey);

      if (amendmentId === updatedValueId) {
        return merge(clone(amendment), updatedValue);
      }
    }

    return amendment;
  });
};

const getIdKey = (amendment) => {
  if (amendment instanceof EmployerBenefit) {
    return "employer_benefit_id";
  } else if (amendment instanceof PreviousLeave) {
    return "previous_leave_id";
  }
};

export default updateAmendment;
