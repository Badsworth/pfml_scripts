import Claim from "../models/Claim";
import ClaimCollection from "../models/ClaimCollection";
import ClaimsApi from "../api/ClaimsApi";
import useCollectionState from "./useCollectionState";
import { useMemo } from "react";

const useClaimsLogic = ({ appErrorsLogic, portalFlow, user }) => {
  // State representing the collection of claims for the current user.
  // Initialize to empty collection, but will eventually store the claims
  // state as API calls are made to fetch the user's claims and/or create
  // new claims
  const {
    collection: claims,
    addItem: addClaim,
    updateItem: setClaim,
    setCollection: setClaims,
  } = useCollectionState(() => new ClaimCollection());

  const claimsApi = useMemo(() => new ClaimsApi({ user }), [user]);

  /**
   * Load all claims for user
   * This must be called before claims are available
   */
  const loadClaims = async () => {
    if (claims) return;

    appErrorsLogic.clearErrors();

    try {
      const { claims } = await claimsApi.getClaims();
      setClaims(claims);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Update the claim in the API and set application errors if any
   * @param {string} application_id - application id for claim
   * @param {object} patchData - subset of claim data that will be updated
   */
  const updateClaim = async (application_id, patchData) => {
    appErrorsLogic.clearErrors();

    try {
      let { claim } = await claimsApi.updateClaim(application_id, patchData);

      // Currently the API doesn't return the claim data in the response
      // so we're manually constructing the body based on client data.
      // We will change the PATCH applications endpoint to return the full
      // application in this ticket: https://lwd.atlassian.net/browse/API-247
      // TODO: Remove workaround once above ticket is complete: https://lwd.atlassian.net/browse/CP-577
      claim = new Claim({
        ...claims.get(application_id),
        ...patchData,
      });
      // </ end workaround >

      setClaim(claim);

      const params = { claim_id: claim.application_id };
      portalFlow.goToNextPage({ claim, user }, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Create the claim in the API. Handles errors and routing.
   * @returns {Promise}
   */
  const createClaim = async () => {
    appErrorsLogic.clearErrors();

    try {
      const { claim, success } = await claimsApi.createClaim();

      if (success) {
        addClaim(claim);

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
   * @param {object} formState - formState representing entier claim
   */
  const submitClaim = async (formState) => {
    appErrorsLogic.clearErrors();

    try {
      const { claim } = await claimsApi.submitClaim(new Claim(formState));
      setClaim(claim);

      const context = { claim, user };
      const params = { claim_id: claim.application_id };
      portalFlow.goToNextPage(context, params);
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
