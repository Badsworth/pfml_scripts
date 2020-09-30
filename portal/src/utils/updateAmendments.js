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
    if (amendment.id === updatedValue.id) {
      return _.merge(_.clone(amendment), updatedValue);
    }

    return amendment;
  });
};

export default updateAmendment;
