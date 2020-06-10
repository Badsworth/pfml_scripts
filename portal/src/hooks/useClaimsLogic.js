import Claim from "../models/Claim";
import ClaimCollection from "../models/ClaimCollection";
import ClaimsApi from "../api/ClaimsApi";
import useCollectionState from "./useCollectionState";
import { useMemo } from "react";

const useClaimsLogic = ({ user }) => {
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

    try {
      const { claims } = await claimsApi.getClaims();

      setClaims(claims);
    } catch (error) {
      // TODO setAppErrors here
    }
  };

  /**
   * Update the claim in the API and set application errors if any
   * @param {string} application_id - application id for claim
   * @param {object} patchData - subset of claim data that will be updated
   */
  const updateClaim = async (application_id, patchData) => {
    try {
      const { claim } = await claimsApi.updateClaim(application_id, patchData);
      setClaim(claim);
    } catch (error) {
      // TODO setAppErrors
    }
  };

  /**
   * Create the claim in the API and set application errors if any
   * @returns {Claim} newly created claim
   */
  const createClaim = async () => {
    try {
      const { claim } = await claimsApi.createClaim();
      addClaim(claim);

      return claim;
    } catch (error) {
      // TODO setAppErrors

      return null;
    }
  };

  /**
   * Submit the claim in the API and set application errors if any
   * @param {object} formState - formState representing entier claim
   */
  const submitClaim = async (formState) => {
    try {
      const { claim } = await claimsApi.submitClaim(new Claim(formState));
      setClaim(claim);
    } catch (error) {
      // TODO setAppErrors
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
