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
    new ClaimCollection()
  );
  const [isLoadingClaims, setIsLoadingClaims] = useState();

  // Pagination info associated with the current collection of claims
  const [paginationMeta, setPaginationMeta] = useState(new PaginationMeta());

  // Track which filters are activated for the collection of claims
  const [activeFilters, setActiveFilters] = useState({});

  /**
   * Load a page of claims for the authenticated user
   * @param {number|string} [pageOffset] - Page number to load
   * @param {{ employer_id: string }} [filters]
   */
  const loadPage = async (pageOffset = 1, filters = {}) => {
    if (
      isLoadingClaims ||
      // Or have we already loaded this page with the same filters?
      (parseInt(paginationMeta.page_offset) === parseInt(pageOffset) &&
        isEqual(activeFilters, filters))
    ) {
      return;
    }

    setIsLoadingClaims(true);
    appErrorsLogic.clearErrors();

    try {
      const { claims, paginationMeta } = await claimsApi.getClaims(
        pageOffset,
        filters
      );

      setClaims(claims);
      setActiveFilters(filters);
      setPaginationMeta(paginationMeta);
      setIsLoadingClaims(false);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  return {
    activeFilters,
    claims,
    isLoadingClaims,
    loadPage,
    paginationMeta,
  };
};

export default useClaimsLogic;
