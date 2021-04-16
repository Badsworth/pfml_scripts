import ClaimCollection from "../models/ClaimCollection";
import ClaimsApi from "../api/ClaimsApi";
import useCollectionState from "./useCollectionState";
import { useState } from "react";

const useClaimsLogic = ({ appErrorsLogic }) => {
  // Collection of claims for the current user.
  // Initialized to empty collection, but will eventually store the claims
  // as API calls are made to fetch the user's claims
  const { collection: claims, setCollection: setClaims } = useCollectionState(
    new ClaimCollection()
  );

  // Track whether the loadAll method has been called. Checking that claims
  // is set isn't sufficient, since it may only include a subset of claims
  const [hasLoadedAll, setHasLoadedAll] = useState(false);

  const claimsApi = new ClaimsApi();

  /**
   * Load all claims for the authenticated user
   * @param {number} page - zero-based page index
   */
  const loadAll = async (page) => {
    if (hasLoadedAll) return;
    appErrorsLogic.clearErrors();

    try {
      const { claims } = await claimsApi.getClaims(page);

      setClaims(claims);
      setHasLoadedAll(true);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  return {
    claims,
    hasLoadedAll,
    loadAll,
  };
};

export default useClaimsLogic;
