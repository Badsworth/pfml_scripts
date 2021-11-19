import { get, isNil } from "lodash";
import { useMemo, useState } from "react";
import { AppErrorsLogic } from "./useAppErrorsLogic";
import { ClaimDocument } from "../models/Document";
import { ClaimsLogic } from "./useClaimsLogic";
import DocumentCollection from "../models/DocumentCollection";
import EmployerClaim from "../models/EmployerClaim";
import EmployersApi from "../api/EmployersApi";
import { LeaveAdminForbiddenError } from "../errors";
import { PortalFlow } from "./usePortalFlow";
import { UsersLogic } from "./useUsersLogic";

const useEmployersLogic = ({
  appErrorsLogic,
  clearClaims,
  portalFlow,
  setUser,
}: {
  appErrorsLogic: AppErrorsLogic;
  clearClaims: ClaimsLogic["clearClaims"];
  portalFlow: PortalFlow;
  setUser: UsersLogic["setUser"];
}) => {
  const [claim, setEmployerClaim] = useState<EmployerClaim | null>(null);
  const [claimDocumentsMap, setClaimDocumentsMap] = useState<
    Map<string, DocumentCollection>
  >(new Map());
  const employersApi = useMemo(() => new EmployersApi(), []);

  /**
   * Associate employer FEIN with logged in user
   */
  const addEmployer = async (data: { employer_fein: string }, next: string) => {
    appErrorsLogic.clearErrors();

    try {
      const employer = await employersApi.addEmployer(data);
      const params = { employer_id: employer.employer_id, next };
      // Setting user to undefined to require fetching updated user_leave_administrators before navigating to Verify Contributions
      setUser(undefined);
      portalFlow.goToNextPage({}, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Retrieve claim from the API and set application errors if any
   */
  const loadClaim = async (absenceId: string) => {
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
            error instanceof Error ? error.message : ""
          )
        );
      } else {
        appErrorsLogic.catchError(error);
      }
    }
  };

  /**
   * Retrieve documents from the API and set application errors if any
   */
  const loadDocuments = async (absenceId: string) => {
    if (claimDocumentsMap.has(absenceId)) return;
    appErrorsLogic.clearErrors();

    try {
      const { documents } = await employersApi.getDocuments(absenceId);
      const loadedClaimDocumentsMap = new Map(claimDocumentsMap.entries());
      loadedClaimDocumentsMap.set(absenceId, documents);

      setClaimDocumentsMap(loadedClaimDocumentsMap);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Load withholding data from the API and set app errors if any.
   */
  const loadWithholding = async (employerId: string) => {
    try {
      return await employersApi.getWithholding(employerId);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Download document from the API and set app errors if any.
   */
  const downloadDocument = async (
    document: ClaimDocument,
    absenceId: string
  ) => {
    appErrorsLogic.clearErrors();
    try {
      return await employersApi.downloadDocument(absenceId, document);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Submit claim review to the API and set application errors if any
   */
  const submitClaimReview = async (
    absenceId: string,
    data: { [key: string]: unknown }
  ) => {
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
   */
  const submitWithholding = async (
    data: {
      employer_id: string;
      withholding_amount: number;
      withholding_quarter: string;
    },
    next?: string
  ) => {
    appErrorsLogic.clearErrors();

    try {
      const { user } = await employersApi.submitWithholding(data);
      const params = { employer_id: data.employer_id, next };
      // Update user state so the employer now shows as verified:
      setUser(user);
      portalFlow.goToNextPage({}, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  return {
    addEmployer,
    claim,
    claimDocumentsMap,
    downloadDocument,
    loadClaim,
    loadDocuments,
    loadWithholding,
    submitClaimReview,
    submitWithholding,
  };
};

export default useEmployersLogic;
