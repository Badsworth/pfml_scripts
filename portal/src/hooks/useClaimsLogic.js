import Claim from "../models/Claim";
import ClaimsApi from "../api/ClaimsApi";
import merge from "lodash/merge";
import useCollectionState from "./useCollectionState";
import { useMemo } from "react";

const useClaimsLogic = ({ appErrorsLogic, portalFlow, user }) => {
  // State representing the collection of claims for the current user.
  // Initialize to empty collection, but will eventually store the claims
  // state as API calls are made to fetch the user's claims and/or create
  // new claims
  const {
    collection: claims,
    // addItem: addClaim, // TODO: uncomment once the workaround in createClaim is removed: https://lwd.atlassian.net/browse/CP-701
    updateItem: setClaim,
    setCollection: setClaims,
  } = useCollectionState(null); // Set initial value to null to lazy load claims

  const claimsApi = useMemo(() => new ClaimsApi({ user }), [user]);

  let isLoadingClaims = false;

  /**
   * Load all claims for user
   * This must be called before claims are available
   * @param {boolean} [forceReload] Whether or not to force a reload of the claims from the API even if the claims have already been loaded. Defaults to false.
   */
  const loadClaims = async (forceReload = false) => {
    if (!user) return;
    if (claims && !forceReload) return;
    if (isLoadingClaims) return;

    isLoadingClaims = true;

    try {
      const { claims } = await claimsApi.getClaims();
      setClaims(claims);
      appErrorsLogic.clearErrors();
    } catch (error) {
      appErrorsLogic.catchError(error);
    }

    isLoadingClaims = false;
  };

  /**
   * Update the claim in the API and set application errors if any
   * @param {string} application_id - application id for claim
   * @param {object} patchData - subset of claim data that will be updated
   */
  const updateClaim = async (application_id, patchData) => {
    if (!user) return;
    try {
      let { claim } = await claimsApi.updateClaim(application_id, patchData);

      // Currently the API doesn't return the claim data in the response
      // so we're manually constructing the body based on client data.
      // We will change the PATCH applications endpoint to return the full
      // application in this ticket: https://lwd.atlassian.net/browse/API-276
      // TODO: Remove workaround once above ticket is complete: https://lwd.atlassian.net/browse/CP-577
      claim = new Claim(merge(claims.get(application_id), patchData));
      // </ end workaround >
      setClaim(claim);
      const params = { claim_id: claim.application_id };
      portalFlow.goToNextPage({ claim, user }, params);

      appErrorsLogic.clearErrors();
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Create the claim in the API. Handles errors and routing.
   * @returns {Promise}
   */
  const createClaim = async () => {
    if (!user) return;
    appErrorsLogic.clearErrors();

    try {
      const { claim, success } = await claimsApi.createClaim();

      if (success) {
        if (!claims) {
          await loadClaims();
        } else {
          // The API currently doesn't return the claim in POST /applications, so for now just reload all the claims
          // TODO: Remove this workaround and use `addClaim(claim)` instead: https://lwd.atlassian.net/browse/CP-701
          // addClaim(claim);
          await loadClaims(true);
        }

        const context = { claim, user };
        const params = { claim_id: claim.application_id };
        portalFlow.goToPageFor("CREATE_CLAIM", context, params);
      }
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Submit the claim in the API and set application errors if any
   * @param {string} application_id - application id for claim
   */
  const submitClaim = async (application_id) => {
    if (!user) return;
    appErrorsLogic.clearErrors();

    try {
      let { claim, success } = await claimsApi.submitClaim(application_id);

      if (success) {
        // Currently the API doesn't return the claim data in the response
        // so we're manually constructing the body based on client data.
        // We will change the PATCH applications endpoint to return the full
        // application in this ticket: https://lwd.atlassian.net/browse/API-276
        // TODO: Remove workaround once above ticket is complete: https://lwd.atlassian.net/browse/CP-577
        claim = new Claim({
          ...claims.get(application_id),
          ...{
            status: "Completed",
          },
        });
        // </ end workaround >

        setClaim(claim);

        const context = { claim, user };
        const params = { claim_id: claim.application_id };
        portalFlow.goToNextPage(context, params);
      }
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  return {
    claims,
    loadClaims,
    createClaim,
    updateClaim,
    submitClaim,
    setClaims,
  };
};

export default useClaimsLogic;
