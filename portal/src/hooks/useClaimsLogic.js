import Claim from "../models/Claim";
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

    try {
      const { claims, success } = await claimsApi.getClaims();
      if (success) {
        setClaims(claims);
        appErrorsLogic.clearErrors();
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
      let { claim, errors, warnings } = await claimsApi.updateClaim(
        application_id,
        patchData
      );

      const issues = getRelevantIssues(errors, warnings, patchData);

      if (issues.length) {
        throw new ValidationError(issues, "claims");
      }

      // TODO (CP-676): Remove workaround once API returns all the fields in our application
      claim = new Claim(merge(claims.get(application_id), patchData));
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
      let { claim, success } = await claimsApi.submitClaim(application_id);

      if (success) {
        // TODO (CP-676): Remove workaround once API returns all the fields in our application
        claim = new Claim({
          ...claims.get(application_id),
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

  /**
   * Submit files to the API and set application errors if any
   * @param {string} application_id - application id for claim
   * @param {array} files - array of objects {id: string, file: File object}
   * @param {string} documentType - category of documents
   */
  const attachDocuments = async (application_id, files, documentType) => {
    if (!user) return;
    appErrorsLogic.clearErrors();
    try {
      const { success } = await claimsApi.attachDocuments(
        application_id,
        files,
        documentType
      );

      if (success) {
        const context = { user };
        const params = { claim_id: application_id };
        portalFlow.goToNextPage(context, params);
      }
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  return {
    attachDocuments,
    claims,
    load,
    create,
    update,
    submit,
    setClaims,
  };
};

export default useClaimsLogic;
