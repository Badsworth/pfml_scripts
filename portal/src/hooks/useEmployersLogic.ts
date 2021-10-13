import { get, isNil } from "lodash";
import { useMemo, useState } from "react";
import EmployersApi from "../api/EmployersApi";
import { LeaveAdminForbiddenError } from "../errors";

const useEmployersLogic = ({
  appErrorsLogic,
  clearClaims,
  portalFlow,
  setUser,
}) => {
  const [claim, setEmployerClaim] = useState(null);
  const [documents, setDocuments] = useState(null);
  const employersApi = useMemo(() => new EmployersApi(), []);

  /**
   * Associate employer FEIN with logged in user
   * @param {object} data - employer's FEIN
   * @param {string} next - query param to navigate to next page
   */
  const addEmployer = async (data, next) => {
    appErrorsLogic.clearErrors();

    try {
      const employer = await employersApi.addEmployer(data);
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'employer_id' does not exist on type 'Use... Remove this comment to see the full error message
      const params = { employer_id: employer.employer_id, next };
      // Setting user to undefined to require fetching updated user_leave_administrators before navigating to Verify Contributions
      setUser(undefined);
      if (employer) portalFlow.goToNextPage({}, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Retrieve claim from the API and set application errors if any
   * @param {string} absenceId - FINEOS absence id
   */
  const loadClaim = async (absenceId) => {
    if (claim && claim.fineos_absence_id === absenceId) return;
    appErrorsLogic.clearErrors();

    try {
      const { claim } = await employersApi.getClaim(absenceId);

      setEmployerClaim(claim);
    } catch (error) {
      const employer_id = get(error, "responseData.employer_id");
      const has_verification_data = get(
        error,
        "responseData.has_verification_data"
      );

      if (!isNil(employer_id) && !isNil(has_verification_data)) {
        appErrorsLogic.catchError(
          new LeaveAdminForbiddenError(
            employer_id,
            has_verification_data,
            error.message
          )
        );
      } else {
        appErrorsLogic.catchError(error);
      }
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
   * Load withholding data from the API and set app errors if any.
   * @param {string} employerId ID of the employer
   * @returns {Object} withholding data
   */
  const loadWithholding = async (employerId) => {
    try {
      return await employersApi.getWithholding(employerId);
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

      // Clear the cached claim data, most notably is_reviewable and
      // managed_requirements, so that the claim's dashboard status
      // routing remain accurate.
      setEmployerClaim(null);
      clearClaims();

      const params = { absence_id: absenceId };
      portalFlow.goToNextPage({}, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Submit withholding data to the API for verification
   * @param {object} data - user info and employer data
   * @param {string} next - query param to navigate to next page
   */
  const submitWithholding = async (data, next) => {
    appErrorsLogic.clearErrors();

    try {
      await employersApi.submitWithholding(data);
      const params = { employer_id: data.employer_id, next };
      // this forces the user to be refetched.
      setUser(undefined);
      portalFlow.goToNextPage({}, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  return {
    addEmployer,
    claim,
    documents,
    downloadDocument,
    loadClaim,
    loadDocuments,
    loadWithholding,
    submitClaimReview,
    submitWithholding,
  };
};

export default useEmployersLogic;
