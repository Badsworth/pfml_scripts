import { useMemo, useState } from "react";
import EmployersApi from "../api/EmployersApi";

const useEmployersLogic = ({ appErrorsLogic, portalFlow }) => {
  const [claim, setClaim] = useState(null);
  const employersApi = useMemo(() => new EmployersApi(), []);

  /**
   * Retrieve claim from the API and set application errors if any
   * @param {string} absenceId - FINEOS absence id
   */
  const load = async (absenceId) => {
    if (claim) return;
    appErrorsLogic.clearErrors();

    try {
      const { claim, success } = await employersApi.getClaim(absenceId);
      if (success) {
        setClaim(claim);
      }
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Submit claim review to the API and set application errors if any
   * @param {string} absenceId - FINEOS absence id
   * @param {object} data - claim review data
   */
  const submit = async (absenceId, data) => {
    appErrorsLogic.clearErrors();

    try {
      await employersApi.submitClaimReview(absenceId, data);
      const params = { absence_id: absenceId };
      portalFlow.goToNextPage({}, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  return {
    claim,
    load,
    submit,
  };
};

export default useEmployersLogic;
