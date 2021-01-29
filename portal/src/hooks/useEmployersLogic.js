import { useMemo, useState } from "react";
import EmployersApi from "../api/EmployersApi";

const useEmployersLogic = ({ appErrorsLogic, portalFlow }) => {
  const [claim, setClaim] = useState(null);
  const [documents, setDocuments] = useState(null);
  const employersApi = useMemo(() => new EmployersApi(), []);

  /**
   * Retrieve claim from the API and set application errors if any
   * @param {string} absenceId - FINEOS absence id
   */
  const loadClaim = async (absenceId) => {
    if (claim) return;
    appErrorsLogic.clearErrors();

    try {
      const { claim } = await employersApi.getClaim(absenceId);

      setClaim(claim);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Retrieve documents from the API and set application errors if any
   * @param {string} absenceId - FINEOS absence id
   */
  const loadDocuments = async (absenceId) => {
    if (documents) return;
    appErrorsLogic.clearErrors();

    try {
      const { documents } = await employersApi.getDocuments(absenceId);

      setDocuments(documents);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Download document from the API and set app errors if any.
   *
   * @param {string} absenceId ID of the Claim
   * @param {Document} document - Document instasnce to download
   * @returns {Blob} file data
   */
  const downloadDocument = async (absenceId, document) => {
    appErrorsLogic.clearErrors();
    try {
      return await employersApi.downloadDocument(absenceId, document);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Submit claim review to the API and set application errors if any
   * @param {string} absenceId - FINEOS absence id
   * @param {object} data - claim review data
   */
  const submitClaimReview = async (absenceId, data) => {
    appErrorsLogic.clearErrors();

    try {
      await employersApi.submitClaimReview(absenceId, data);
      const params = { absence_id: absenceId };
      portalFlow.goToNextPage({}, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Submit withholding data to the API for verification
   * @param {object} data - user info and employer data
   */
  const submitWithholding = async (data) => {
    appErrorsLogic.clearErrors();

    try {
      await employersApi.submitWithholding(data);
      const params = { employer_id: data.employer_id };
      portalFlow.goToNextPage({}, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  return {
    claim,
    documents,
    downloadDocument,
    loadClaim,
    loadDocuments,
    submitClaimReview,
    submitWithholding,
  };
};

export default useEmployersLogic;
