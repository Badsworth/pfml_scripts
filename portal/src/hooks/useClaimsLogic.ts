import ClaimDetail, { PaymentDetail, Payments } from "../models/ClaimDetail";
import { ClaimWithdrawnError, ValidationError } from "../errors";
import ApiResourceCollection from "../models/ApiResourceCollection";
import { AppErrorsLogic } from "./useAppErrorsLogic";
import Claim from "../models/Claim";
import ClaimsApi from "../api/ClaimsApi";
import PaginationMeta from "../models/PaginationMeta";
import { PortalFlow } from "./usePortalFlow";
import { isEqual } from "lodash";
import { isFeatureEnabled } from "../services/featureFlags";
import useCollectionState from "./useCollectionState";
import { useState } from "react";

const useClaimsLogic = ({
  appErrorsLogic,
  portalFlow,
}: {
  appErrorsLogic: AppErrorsLogic;
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

  // Payments data associated with claim
  const [loadedPaymentsData, setLoadedPaymentsData] = useState<Payments>();

  /**
   * Check if payments have loaded for claim
   */
  const hasLoadedPayments = (absenceId: string) =>
    loadedPaymentsData?.absence_case_id === absenceId;

  // Track the search and filter params currently applied for the collection of claims
  const [activeFilters, setActiveFilters] = useState({});

  // Track the order params currently applied for the collection of claims
  const [activeOrder, setActiveOrder] = useState({});

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
   * @param [pageOffset] - Page number to load
   * @param [filters.claim_status] - Comma-separated list of statuses
   */
  const loadPage = async (
    pageOffset: number | string = 1,
    order: {
      order_by?: string;
      order_direction?: "ascending" | "descending";
    } = {},
    filters: {
      claim_status?: string;
      employer_id?: string;
      search?: string;
    } = {}
  ) => {
    if (isLoadingClaims) return;

    // Or have we already loaded this page with the same order and filter params?
    if (
      paginationMeta.page_offset === Number(pageOffset) &&
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
   * @returns claim detail if we were able to load it. Returns undefined if
   * we're already loading a claim detail or if the request to load the claim detail fails.
   */
  const loadClaimDetail = async (absenceId: string) => {
    if (isLoadingClaimDetail) return;

    const shouldPaymentsLoad =
      isFeatureEnabled("claimantShowPaymentsPhaseTwo") &&
      claimDetail?.hasApprovedStatus &&
      portalFlow.pageRoute === "/applications/status/payments" &&
      !hasLoadedPayments(absenceId);

    let loadedClaimDetail = claimDetail;
    // Have we already loaded this claim? If claim is loaded we check for payments being loaded as well
    if (claimDetail?.fineos_absence_id === absenceId) {
      if (shouldPaymentsLoad) {
        try {
          const claimDetailWithPayments = await fetchPayments(
            absenceId,
            claimDetail
          );
          setClaimDetail(claimDetailWithPayments);
          return claimDetailWithPayments;
        } catch (error) {
          appErrorsLogic.catchError(error);
        } finally {
          setIsLoadingClaimDetail(false);
        }
      }
    } else {
      try {
        setIsLoadingClaimDetail(true);
        appErrorsLogic.clearErrors();
        const data = await claimsApi.getClaimDetail(absenceId);
        loadedClaimDetail = data.claimDetail;
        if (shouldPaymentsLoad) {
          const claimDetailWithPayments = fetchPayments(absenceId, claimDetail);
          setClaimDetail(await claimDetailWithPayments);
          return claimDetailWithPayments;
        }
        setClaimDetail(loadedClaimDetail);
      } catch (error) {
        if (
          error instanceof ValidationError &&
          error.issues[0].type === "fineos_claim_withdrawn"
        ) {
          // The claim was withdrawn -- we'll need to show an error message to the user
          appErrorsLogic.catchError(
            new ClaimWithdrawnError(absenceId, error.issues[0])
          );
        } else {
          appErrorsLogic.catchError(error);
        }
      } finally {
        setIsLoadingClaimDetail(false);
      }
    }
    return loadedClaimDetail;
  };

  const fetchPayments = async (
    absenceId: string,
    loadedClaim: Partial<ClaimDetail> | undefined
  ) => {
    let paymentList: PaymentDetail[] = [];
    try {
      const fetchedPayments = await claimsApi.getPayments(absenceId);
      paymentList = fetchedPayments.payments;
    } catch (error) {
      appErrorsLogic.catchError(error);
    } finally {
      setLoadedPaymentsData({
        payments: paymentList,
        absence_case_id: absenceId,
      });
    }
    if (loadedClaim) {
      loadedClaim.payments = paymentList;
    }
    return new ClaimDetail(loadedClaim);
  };

  return {
    activeFilters,
    claimDetail,
    claims,
    clearClaims,
    isLoadingClaims,
    isLoadingClaimDetail,
    loadClaimDetail,
    loadedPaymentsData,
    loadPage,
    paginationMeta,
    hasLoadedPayments,
  };
};

export default useClaimsLogic;
export type ClaimsLogic = ReturnType<typeof useClaimsLogic>;
