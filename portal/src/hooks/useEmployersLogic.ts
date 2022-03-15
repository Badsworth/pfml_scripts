import { useMemo, useState } from "react";
import ApiResourceCollection from "../models/ApiResourceCollection";
import { ClaimDocument } from "../models/Document";
import { ClaimsLogic } from "./useClaimsLogic";
import EmployerClaim from "../models/EmployerClaim";
import EmployersApi from "../api/EmployersApi";
import { ErrorsLogic } from "./useErrorsLogic";
import { PortalFlow } from "./usePortalFlow";
import { UsersLogic } from "./useUsersLogic";
import { get } from "lodash";
import routes from "../routes";
import tracker from "../services/tracker";

const useEmployersLogic = ({
  errorsLogic,
  clearClaims,
  portalFlow,
  setUser,
}: {
  errorsLogic: ErrorsLogic;
  clearClaims: ClaimsLogic["clearClaims"];
  portalFlow: PortalFlow;
  setUser: UsersLogic["setUser"];
}) => {
  const [claim, setEmployerClaim] = useState<EmployerClaim | null>(null);
  const [claimDocumentsMap, setClaimDocumentsMap] = useState<
    Map<string, ApiResourceCollection<ClaimDocument>>
  >(new Map());
  const employersApi = useMemo(() => new EmployersApi(), []);

  /**
   * Associate employer FEIN with logged in user
   */
  const addEmployer = async (data: { employer_fein: string }, next: string) => {
    errorsLogic.clearErrors();

    try {
      const employer = await employersApi.addEmployer(data);
      const params = { employer_id: employer.employer_id, next };
      // Setting user to undefined to require fetching updated user_leave_administrators before navigating to Verify Contributions
      setUser(undefined);
      portalFlow.goToNextPage({}, params);
    } catch (error) {
      errorsLogic.catchError(error);
    }
  };

  /**
   * Retrieve claim from the API and set application errors if any
   */
  const loadClaim = async (absenceId: string) => {
    if (claim && claim.fineos_absence_id === absenceId) return;
    errorsLogic.clearErrors();

    try {
      const { claim } = await employersApi.getClaim(absenceId);

      setEmployerClaim(claim);
    } catch (error) {
      const employer_id = get(error, "responseData.employer_id");
      const has_verification_data = get(
        error,
        "responseData.has_verification_data"
      );

      if (
        typeof employer_id === "string" &&
        typeof has_verification_data === "boolean"
      ) {
        // Leave admin was prevented from loading the claim, which we interpret to mean
        // as they need to still verify their organization:
        handleUnverifiedLeaveAdmin(employer_id, has_verification_data);
      } else {
        errorsLogic.catchError(error);
      }
    }
  };

  /**
   * Retrieve documents from the API and set application errors if any
   */
  const loadDocuments = async (absenceId: string) => {
    if (claimDocumentsMap.has(absenceId)) return;
    errorsLogic.clearErrors();

    try {
      const { documents } = await employersApi.getDocuments(absenceId);
      const loadedClaimDocumentsMap = new Map(claimDocumentsMap.entries());
      loadedClaimDocumentsMap.set(absenceId, documents);

      setClaimDocumentsMap(loadedClaimDocumentsMap);
    } catch (error) {
      errorsLogic.catchError(error);
    }
  };

  /**
   * Load withholding data from the API and set app errors if any.
   */
  const loadWithholding = async (employerId: string) => {
    try {
      return await employersApi.getWithholding(employerId);
    } catch (error) {
      errorsLogic.catchError(error);
    }
  };

  /**
   * Download document from the API and set app errors if any.
   */
  const downloadDocument = async (
    document: ClaimDocument,
    absenceId: string
  ) => {
    errorsLogic.clearErrors();
    try {
      return await employersApi.downloadDocument(absenceId, document);
    } catch (error) {
      errorsLogic.catchError(error);
    }
  };

  /**
   * Submit claim review to the API and set application errors if any
   */
  const submitClaimReview = async (
    absenceId: string,
    data: { [key: string]: unknown }
  ) => {
    errorsLogic.clearErrors();

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
      errorsLogic.catchError(error);
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
    errorsLogic.clearErrors();

    try {
      const { user } = await employersApi.submitWithholding(data);
      const params = { employer_id: data.employer_id, next };
      // Update user state so the employer now shows as verified:
      setUser(user);
      portalFlow.goToNextPage({}, params);
    } catch (error) {
      errorsLogic.catchError(error);
    }
  };

  /**
   * Redirect to either the Verify Contributions or Cannot Verify page
   * based on if the UserLeaveAdministrator is verifiable.
   */
  const handleUnverifiedLeaveAdmin = (
    employer_id: string,
    has_verification_data: boolean
  ) => {
    tracker.trackEvent("LeaveAdminForbiddenError", {
      employerId: employer_id,
      hasVerificationData: has_verification_data.toString(),
    });

    if (has_verification_data) {
      portalFlow.goTo(
        routes.employers.verifyContributions,
        {
          employer_id,
          next: portalFlow.pathWithParams,
        },
        { redirect: true }
      );
    } else {
      portalFlow.goTo(
        routes.employers.cannotVerify,
        {
          employer_id,
        },
        { redirect: true }
      );
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
