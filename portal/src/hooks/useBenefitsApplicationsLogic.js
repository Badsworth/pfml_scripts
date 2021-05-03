import { NotFoundError, ValidationError } from "../errors";
import { useMemo, useState } from "react";

import BenefitsApplicationCollection from "../models/BenefitsApplicationCollection";
import BenefitsApplicationsApi from "../api/BenefitsApplicationsApi";
import OccupationsApi from "../api/OccupationsApi";
import getRelevantIssues from "../utils/getRelevantIssues";
import routes from "../routes";
import useCollectionState from "./useCollectionState";

const useBenefitsApplicationsLogic = ({ appErrorsLogic, portalFlow, user }) => {
  // State representing the collection of applications for the current user.
  // Initialize to empty collection, but will eventually store the applications
  // state as API calls are made to fetch the user's applications and/or create
  // new applications
  const {
    collection: benefitsApplications,
    addItem: addBenefitsApplication,
    updateItem: setBenefitsApplication,
    setCollection: setBenefitsApplications,
  } = useCollectionState(new BenefitsApplicationCollection());

  // Track whether the loadAll method has been called. Checking that claims
  // is set isn't sufficient, since it may only include a subset of applications
  // if loadAll hasn't been called yet
  const [hasLoadedAll, setHasLoadedAll] = useState(false);

  const claimsApi = useMemo(() => new BenefitsApplicationsApi({ user }), [
    user,
  ]);

  const occupationsApi = useMemo(() => new OccupationsApi({ user }), [user]);

  // Cache the validation warnings associated with each claim. Primarily
  // used for controlling the status of Checklist steps.
  const [warningsLists, setWarningsLists] = useState({});

  /**
   * Store warnings for a specific claim
   * @param {string} application_id
   * @param {Array} warnings
   * @private
   */
  const setClaimWarnings = (application_id, warnings) => {
    setWarningsLists((prevWarningsList) => {
      return {
        ...prevWarningsList,
        [application_id]: warnings,
      };
    });
  };

  /**
   * Check if a claim and its warnings have been loaded. This helps
   * our withBenefitsApplication higher-order component accurately display a loading state.
   *
   * @param {string} application_id
   * @returns {boolean}
   */
  const hasLoadedBenefitsApplicationAndWarnings = (application_id) => {
    // !! so we always return a Boolean
    return !!(
      warningsLists.hasOwnProperty(application_id) &&
      benefitsApplications.getItem(application_id)
    );
  };

  /**
   * Load a single claim
   * @param {string} application_id - ID of claim to load
   */
  const load = async (application_id) => {
    if (!user) throw new Error("Cannot load claim before user is loaded");

    // Skip API request if we already have the claim AND its validation warnings.
    // It's important we load the claim if warnings haven't been fetched yet,
    // since the Checklist needs those to be present in order to accurately
    // determine what steps are completed.
    if (
      benefitsApplications &&
      hasLoadedBenefitsApplicationAndWarnings(application_id)
    )
      return;

    appErrorsLogic.clearErrors();

    try {
      const { claim, warnings } = await claimsApi.getClaim(application_id);

      if (benefitsApplications.getItem(application_id)) {
        setBenefitsApplication(claim);
      } else {
        addBenefitsApplication(claim);
      }

      setClaimWarnings(application_id, warnings);
    } catch (error) {
      if (error instanceof NotFoundError) {
        portalFlow.goTo(routes.applications.index);
        return;
      }

      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Load all claims for the authenticated user
   */
  const loadAll = async () => {
    if (!user) throw new Error("Cannot load claims before user is loaded");
    if (hasLoadedAll) return;

    appErrorsLogic.clearErrors();

    try {
      const { claims } = await claimsApi.getClaims();

      setBenefitsApplications(claims);
      setHasLoadedAll(true);
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

      setBenefitsApplication(claim);
      setClaimWarnings(application_id, warnings);

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
      const { claim } = await claimsApi.completeClaim(application_id);

      setBenefitsApplication(claim);
      const context = { claim, user };
      const params = { claim_id: claim.application_id };
      portalFlow.goToNextPage(context, params);
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
      const { claim } = await claimsApi.createClaim();

      addBenefitsApplication(claim);

      const context = { claim, user };
      const params = { claim_id: claim.application_id };
      portalFlow.goToPageFor("CREATE_CLAIM", context, params);
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
      const { claim } = await claimsApi.submitClaim(application_id);

      setBenefitsApplication(claim);

      const context = { claim, user };
      const params = {
        claim_id: claim.application_id,
        "part-one-submitted": "true",
      };
      portalFlow.goToNextPage(context, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  const submitPaymentPreference = async (
    application_id,
    paymentPreferenceData
  ) => {
    if (!user) return;
    appErrorsLogic.clearErrors();

    try {
      const {
        claim,
        errors,
        warnings,
      } = await claimsApi.submitPaymentPreference(
        application_id,
        paymentPreferenceData
      );

      // This endpoint should only return errors relevant to this page so no need to filter
      const issues = getRelevantIssues(errors, warnings, []);

      if (errors && errors.length) {
        throw new ValidationError(issues, "claims");
      }

      setBenefitsApplication(claim);
      setClaimWarnings(application_id, warnings);

      if (issues && issues.length) {
        throw new ValidationError(issues, "claims");
      }

      const context = { claim, user };
      const params = {
        claim_id: claim.application_id,
        "payment-pref-submitted": "true",
      };
      portalFlow.goToNextPage(context, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  const getOccupations = async () => {
    return await occupationsApi.getAll();
  };

  const getOccupationTitles = async (occupation_id) => {
    return await occupationsApi.getTitlesById(parseInt(occupation_id));
  };

  return {
    benefitsApplications,
    complete,
    create,
    hasLoadedAll,
    hasLoadedBenefitsApplicationAndWarnings,
    load,
    loadAll,
    update,
    submit,
    submitPaymentPreference,
    warningsLists,
    getOccupations,
    getOccupationTitles,
  };
};

export default useBenefitsApplicationsLogic;
