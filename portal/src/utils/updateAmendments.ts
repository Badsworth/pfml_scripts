import { clone, get, merge } from "lodash";
import EmployerBenefit from "../models/EmployerBenefit";
import PreviousLeave from "../models/PreviousLeave";

/**
 * Returns an updated array (for employer benefits or previous leaves) with amended data
 */
const updateAmendments = (
  amendments: EmployerBenefit[] | PreviousLeave[],
  updatedValue: Record<string, unknown> | EmployerBenefit | PreviousLeave
) => {
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

const getIdKey = (amendment: EmployerBenefit | PreviousLeave) => {
  if (amendment instanceof EmployerBenefit) {
    return "employer_benefit_id";
  } else if (amendment instanceof PreviousLeave) {
    return "previous_leave_id";
  }
};

export default updateAmendments;
