import ClaimCollection from "../models/ClaimCollection";
import ClaimsApi from "../api/ClaimsApi";
import PaginationMeta from "../models/PaginationMeta";
import useCollectionState from "./useCollectionState";
import { useState } from "react";

const useClaimsLogic = ({ appErrorsLogic }) => {
  // Collection of claims for the current user.
  // Initialized to empty collection, but will eventually store the claims
  // as API calls are made to fetch the user's claims
  const { collection: claims, setCollection: setClaims } = useCollectionState(
    new ClaimCollection()
  );
  // Pagination info associated with the current collection of claims
  const [paginationMeta, setPaginationMeta] = useState(new PaginationMeta());
  const claimsApi = new ClaimsApi();

  /**
   * Load a page of claims for the authenticated user
   * @param {number} pageOffset - Page number to load
   */
  const loadPage = async (pageOffset = 1) => {
    if (paginationMeta.page_offset === pageOffset) return;
    appErrorsLogic.clearErrors();

    try {
      const { claims, paginationMeta } = await claimsApi.getClaims(pageOffset);

      setClaims(claims);
      setPaginationMeta(paginationMeta);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  return {
    claims,
    loadPage,
    paginationMeta,
  };
};

export default useClaimsLogic;
