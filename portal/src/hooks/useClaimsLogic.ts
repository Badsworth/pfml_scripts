import {
  ClaimDetailLoadError,
  ClaimWithdrawnError,
  ValidationError,
} from "../errors";
import ClaimCollection from "../models/ClaimCollection";
import ClaimsApi from "../api/ClaimsApi";
import PaginationMeta from "../models/PaginationMeta";
import { isEqual } from "lodash";
import useCollectionState from "./useCollectionState";
import { useState } from "react";

const useClaimsLogic = ({ appErrorsLogic }) => {
  const claimsApi = new ClaimsApi();

  // Collection of claims for the current user.
  // Initialized to empty collection, but will eventually store the claims
  // as API calls are made to fetch the user's claims
  const { collection: claims, setCollection: setClaims } = useCollectionState(
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
    new ClaimCollection()
  );
  const [claimDetail, setClaimDetail] = useState();
  const [isLoadingClaims, setIsLoadingClaims] = useState<boolean>();
  const [isLoadingClaimDetail, setIsLoadingClaimDetail] = useState<boolean>();

  // Pagination info associated with the current collection of claims
  const [paginationMeta, setPaginationMeta] = useState(new PaginationMeta());

  // Track the search and filter params currently applied for the collection of claims
  const [activeFilters, setActiveFilters] = useState({});

  // Track the order params currently applied for the collection of claims
  const [activeOrder, setActiveOrder] = useState({});

  /**
   * Empty the claims collection so that it is fetched again from the API
   */
  const clearClaims = () => {
    // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
    setClaims(new ClaimCollection());
    // Also clear any indication that a page is loaded, so our loadPage method
    // fetches the page from the API
    setPaginationMeta(new PaginationMeta());
  };

  /**
   * Load a page of claims for the authenticated user
   * @param {number|string} [pageOffset] - Page number to load
   * @param {object} [order]
   * @param {string} [order.order_by]
   * @param {string} [order.order_direction]
   * @param {object} [filters]
   * @param {string} [filters.claim_status] - Comma-separated list of statuses
   * @param {string} [filters.employer_id]
   * @param {string} [filters.search]
   */
  const loadPage = async (pageOffset = 1, order = {}, filters = {}) => {
    if (isLoadingClaims) return;

    // Or have we already loaded this page with the same order and filter params?
    if (
      // @ts-expect-error ts-migrate(2339) FIXME: Property 'page_offset' does not exist on type 'Pag... Remove this comment to see the full error message
      parseInt(paginationMeta.page_offset) === parseInt(pageOffset) &&
      isEqual(activeFilters, filters) &&
      isEqual(activeOrder, order)
    ) {
      return;
    }

    setIsLoadingClaims(true);
    appErrorsLogic.clearErrors();

    try {
      const { claims, paginationMeta } = await claimsApi.getClaims(
        pageOffset,
        order,
        filters
      );

      setClaims(claims);
      setActiveFilters(filters);
      setActiveOrder(order);
      setPaginationMeta(paginationMeta);
      setIsLoadingClaims(false);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Load details for a single claim. Note that if there is already a claim detail being loaded then
   * this function will immediately return undefined.
   * @param {string} absenceId - FINEOS absence ID for the claim to load
   * @returns {ClaimDetail|undefined} claim detail if we were able to load it. Returns undefined if
   * we're already loading a claim detail or if the request to load the claim detail fails.
   */
  const loadClaimDetail = async (absenceId) => {
    if (isLoadingClaimDetail) return;

    // Have we already loaded this claim?
    // @ts-expect-error ts-migrate(2532) FIXME: Object is possibly 'undefined'.
    if (claimDetail?.fineos_absence_id === absenceId) {
      return claimDetail;
    }

    setIsLoadingClaimDetail(true);
    appErrorsLogic.clearErrors();

    let loadedClaimDetail;
    try {
      const data = await claimsApi.getClaimDetail(absenceId);
      loadedClaimDetail = data.claimDetail;

      setClaimDetail(loadedClaimDetail);
    } catch (error) {
      if (
        error instanceof ValidationError &&
        // @ts-expect-error ts-migrate(2339) FIXME: Property 'issues' does not exist on type 'Validati... Remove this comment to see the full error message
        error.issues[0].type === "fineos_claim_withdrawn"
      ) {
        // The claim was withdrawn -- we'll need to show an error message to the user
        appErrorsLogic.catchError(
          // @ts-expect-error ts-migrate(2339) FIXME: Property 'issues' does not exist on type 'Validati... Remove this comment to see the full error message
          new ClaimWithdrawnError(absenceId, error.issues[0])
        );
      } else {
        appErrorsLogic.catchError(new ClaimDetailLoadError(absenceId));
      }
    } finally {
      setIsLoadingClaimDetail(false);
    }

    return loadedClaimDetail;
  };

  return {
    activeFilters,
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
