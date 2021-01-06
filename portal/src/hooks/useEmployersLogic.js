import { useMemo, useState } from "react";
import EmployersApi from "../api/EmployersApi";
import routes from "../routes";

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
  const submit = async (absenceId, data) => {
    appErrorsLogic.clearErrors();

    try {
      await employersApi.submitClaimReview(absenceId, data);
      const params = { absence_id: absenceId };
      portalFlow.goToNextPage({}, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
      // Cognito error due to expired user session
      // Redirect to login; upon successful login, redirect back to Review page
      // TODO (EMPLOYER-724): Move logic to handle scenario throughout Portal
      if (error === "No current user") {
        const { pathWithParams } = portalFlow;
        portalFlow.goTo(routes.auth.login, { next: pathWithParams });
      }
    }
  };

  return {
    claim,
    documents,
    downloadDocument,
    loadClaim,
    loadDocuments,
    submit,
  };
};

export default useEmployersLogic;
