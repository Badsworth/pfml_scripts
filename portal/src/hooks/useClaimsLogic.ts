import { ClaimWithdrawnError, ValidationError } from "../errors";
import ClaimsApi, { GetClaimsParams } from "../api/ClaimsApi";
import ApiResourceCollection from "../models/ApiResourceCollection";
import Claim from "../models/Claim";
import ClaimDetail from "../models/ClaimDetail";
import { ErrorsLogic } from "./useErrorsLogic";
import PaginationMeta from "../models/PaginationMeta";
import { PortalFlow } from "./usePortalFlow";
import { isEqual } from "lodash";
import useCollectionState from "./useCollectionState";
import { useState } from "react";

const useClaimsLogic = ({
  errorsLogic,
}: {
  errorsLogic: ErrorsLogic;
  portalFlow: PortalFlow;
}) => {
  const claimsApi = new ClaimsApi();

  // Collection of claims for the current user.
  // Initialized to empty collection, but will eventually store the claims
  // as API calls are made to fetch the user's claims
  const { collection: claims, setCollection: setClaims } = useCollectionState(
    new ApiResourceCollection<Claim>("fineos_absence_id")
  );
  const [claimDetail, setClaimDetail] = useState<ClaimDetail>();
  const [isLoadingClaims, setIsLoadingClaims] = useState<boolean>();
  const [isLoadingClaimDetail, setIsLoadingClaimDetail] = useState<boolean>();

  // Pagination info associated with the current collection of claims
  const [paginationMeta, setPaginationMeta] = useState<
    PaginationMeta | { [key: string]: never }
  >({});

  // Track params currently applied for the collection of claims
  const [activeParams, setActiveParams] = useState({});

  /**
   * Empty the claims collection so that it is fetched again from the API
   */
  const clearClaims = () => {
    setClaims(new ApiResourceCollection<Claim>("fineos_absence_id"));
    // Also clear any indication that a page is loaded, so our loadPage method
    // fetches the page from the API
    setPaginationMeta({});
  };

  /**
   * Load a page of claims for the authenticated user
   */
  const loadPage = async (queryParams: GetClaimsParams = {}) => {
    if (isLoadingClaims) return;

    // Or have we already loaded this page with the same order and filter params?
    if (isEqual(activeParams, queryParams)) {
      return;
    }

    setIsLoadingClaims(true);
    errorsLogic.clearErrors();

    try {
      const { claims, paginationMeta } = await claimsApi.getClaims(queryParams);
      setClaims(claims);
      setActiveParams(queryParams);
      setPaginationMeta(paginationMeta);
      setIsLoadingClaims(false);
    } catch (error) {
      errorsLogic.catchError(error);
    }
  };

  /**
   * Load details for a single claim. Note that if there is already a claim detail being loaded then
   * this function will immediately return undefined.
   * @returns claim detail if we were able to load it. Returns undefined if
   * we're already loading a claim detail or if the request to load the claim detail fails.
   */
  const loadClaimDetail = async (absenceId: string) => {
    if (isLoadingClaimDetail) return;

    if (claimDetail?.fineos_absence_id !== absenceId) {
      try {
        setIsLoadingClaimDetail(true);
        errorsLogic.clearErrors();
        const data = await claimsApi.getClaimDetail(absenceId);
        setClaimDetail(new ClaimDetail(data.claimDetail));
      } catch (error) {
        if (
          error instanceof ValidationError &&
          error.issues[0].type === "fineos_claim_withdrawn"
        ) {
          // The claim was withdrawn -- we'll need to show an error message to the user
          errorsLogic.catchError(
            new ClaimWithdrawnError(absenceId, error.issues[0])
          );
        } else {
          errorsLogic.catchError(error);
        }
      } finally {
        setIsLoadingClaimDetail(false);
      }
    }
  };

  return {
    claimDetail,
    claims,
    clearClaims,
    isLoadingClaims,
    isLoadingClaimDetail,
    loadClaimDetail,
    loadPage,
    paginationMeta,
  };
};

export default useClaimsLogic;
export type ClaimsLogic = ReturnType<typeof useClaimsLogic>;
