import EmployersApi from "../api/EmployersApi";
import { useMemo } from "react";

const useEmployersLogic = ({ appErrorsLogic, portalFlow }) => {
  const employersApi = useMemo(() => new EmployersApi(), []);

  /**
   * Submit claim review to the API and set application errors if any
   * @param {string} absenceId - FINEOS absence id
   * @param {object} data - claim review data
   */
  const submit = async (absenceId, data) => {
    appErrorsLogic.clearErrors();

    try {
      const { success } = await employersApi.submitClaimReview(absenceId, data);
      if (success) {
        const params = { absence_id: absenceId };
        portalFlow.goToNextPage({}, params);
      }
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  return {
    submit,
  };
};

export default useEmployersLogic;
