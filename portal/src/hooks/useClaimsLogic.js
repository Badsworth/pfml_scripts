import ClaimsApi from "../api/ClaimsApi";
import { ValidationError } from "../errors";
import getRelevantIssues from "../utils/getRelevantIssues";
import { merge } from "lodash";
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
  } = useCollectionState(null); // Set initial value to null to lazy load claims

  const claimsApi = useMemo(() => new ClaimsApi({ user }), [user]);

  /**
   * Load all claims for user
   * This must be called before claims are available
   */
  const load = async () => {
    if (!user) throw new Error("Cannot load claims before user is loaded");
    if (claims) return;
    appErrorsLogic.clearErrors();

    try {
      const { claims, success } = await claimsApi.getClaims();

      if (success) {
        setClaims(claims);
      }
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Update the claim in the API and set application errors if any
   * @param {string} application_id - application id for claim
   * @param {object} patchData - subset of claim data that will be updated, and
   * used as the list of fields to filter validation warnings by
   */
  const update = async (application_id, patchData) => {
    if (!user) return;
    appErrorsLogic.clearErrors();

    try {
      const { claim, errors, warnings } = await claimsApi.updateClaim(
        application_id,
        patchData
      );

      const issues = getRelevantIssues(errors, warnings, [portalFlow.page]);

      // If there were any validation errors, then throw *before*
      // the claim is updated in our state, to avoid overriding
      // the user's in-progress answers
      if (errors && errors.length) {
        throw new ValidationError(issues, "claims");
      }

      // TODO (CP-676): Remove workaround once API returns all the fields in our application
      if (patchData.temp) {
        const { temp } = claims.get(claim.application_id);
        claim.temp = merge(temp, patchData.temp);
      }
      // </ end workaround >

      setClaim(claim);

      // If there were only validation warnings, then throw *after*
      // the claim has been updated in our state, so our local claim
      // state remains consistent with the claim state stored in the API,
      // which still received the updates in the request. This is important
      // for situations like leave periods, where the API passes us back
      // a leave_period_id field for making subsequent updates.
      if (issues.length) {
        throw new ValidationError(issues, "claims");
      }

      const params = { claim_id: claim.application_id };
      portalFlow.goToNextPage({ claim, user }, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Complete the claim in the API
   * @param {string} application_id
   */
  const complete = async (application_id) => {
    if (!user) return;
    appErrorsLogic.clearErrors();

    try {
      const { claim, success } = await claimsApi.completeClaim(application_id);

      if (success) {
        setClaim(claim);
        const context = { claim, user };
        const params = { claim_id: claim.application_id };
        portalFlow.goToNextPage(context, params);
      }
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Create the claim in the API. Handles errors and routing.
   * @returns {Promise}
   */
  const create = async () => {
    if (!user) return;
    appErrorsLogic.clearErrors();

    try {
      const { claim, success } = await claimsApi.createClaim();

      if (success) {
        if (!claims) {
          await load();
        } else {
          addClaim(claim);
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
  const submit = async (application_id) => {
    if (!user) return;
    appErrorsLogic.clearErrors();

    try {
      const { claim, success } = await claimsApi.submitClaim(application_id);

      if (success) {
        // TODO (CP-676): Remove workaround once API returns all the fields in our application
        claim.temp = claims.get(claim.application_id).temp;
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
    complete,
    load,
    create,
    update,
    submit,
    setClaims,
  };
};

export default useClaimsLogic;
