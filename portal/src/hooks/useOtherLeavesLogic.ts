import OtherLeavesApi from "../api/OtherLeavesApi";
import assert from "assert";

const useOtherLeavesLogic = ({ appErrorsLogic }) => {
  const otherLeavesApi = new OtherLeavesApi();

  /**
   * Remove an existing employer benefit
   * @param {string} applicationId - application id for claim
   * @param {string} employerBenefitId - employer benefit id which is to be removed
   * @returns {bool} true if successful; false if not. Errors are caught and sent to
   * appErrorsLogic.
   */
  const removeEmployerBenefit = async (applicationId, employerBenefitId) => {
    assert(applicationId);
    assert(employerBenefitId);
    appErrorsLogic.clearErrors();

    try {
      await otherLeavesApi.removeEmployerBenefit(
        applicationId,
        employerBenefitId
      );
    } catch (error) {
      appErrorsLogic.catchError(error);
      return false;
    }
    return true;
  };

  /**
   * Remove an existing other income
   * @param {string} applicationId - application id for claim
   * @param {string} otherIncomeId - other income id which is to be removed
   * @returns {bool} true if successful; false if not. Errors are caught and sent to
   * appErrorsLogic.
   */
  const removeOtherIncome = async (applicationId, otherIncomeId) => {
    assert(applicationId);
    assert(otherIncomeId);
    appErrorsLogic.clearErrors();

    try {
      await otherLeavesApi.removeOtherIncome(applicationId, otherIncomeId);
    } catch (error) {
      appErrorsLogic.catchError(error);
      return false;
    }
    return true;
  };

  /**
   * Remove an existing previous leave
   * @param {string} applicationId - application id for claim
   * @param {string} previousLeaveId - previous leave id which is to be removed
   * @returns {bool} true if successful; false if not. Errors are caught and sent to
   * appErrorsLogic.
   */
  const removePreviousLeave = async (applicationId, previousLeaveId) => {
    assert(applicationId);
    assert(previousLeaveId);
    appErrorsLogic.clearErrors();

    try {
      await otherLeavesApi.removePreviousLeave(applicationId, previousLeaveId);
    } catch (error) {
      appErrorsLogic.catchError(error);
      return false;
    }
    return true;
  };

  return {
    removeEmployerBenefit,
    removeOtherIncome,
    removePreviousLeave,
  };
};

export default useOtherLeavesLogic;
