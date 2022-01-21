import { Issue, NotFoundError, ValidationError } from "../errors";
import { AppErrorsLogic } from "./useAppErrorsLogic";
import BenefitsApplication from "../models/BenefitsApplication";
import BenefitsApplicationCollection from "../models/BenefitsApplicationCollection";
import BenefitsApplicationsApi from "../api/BenefitsApplicationsApi";
import { NullableQueryParams } from "../utils/routeWithParams";
import PaginationMeta from "../models/PaginationMeta";
import PaymentPreference from "../models/PaymentPreference";
import { PortalFlow } from "./usePortalFlow";
import TaxWithholdingPreference from "../models/TaxWithholdingPreference";
import getRelevantIssues from "../utils/getRelevantIssues";
import routes from "../routes";
import useCollectionState from "./useCollectionState";
import { useState } from "react";

const useBenefitsApplicationsLogic = ({
  appErrorsLogic,
  portalFlow,
}: {
  appErrorsLogic: AppErrorsLogic;
  portalFlow: PortalFlow;
}) => {
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

  // Tracks loading state of claims when calling loadPage()
  const [isLoadingClaims, setIsLoadingClaims] = useState<boolean>();

  // Pagination info associated with the current collection of claims
  const [paginationMeta, setPaginationMeta] = useState<
    PaginationMeta | { [key: string]: never }
  >({});

  const applicationsApi = new BenefitsApplicationsApi();

  // Cache the validation warnings associated with each claim. Primarily
  // used for controlling the status of Checklist steps.
  const [warningsLists, setWarningsLists] = useState<{
    [application_id: string]: Issue[];
  }>({});

  /**
   * Store warnings for a specific claim
   */
  const setClaimWarnings = (application_id: string, warnings: Issue[]) => {
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
   */
  const hasLoadedBenefitsApplicationAndWarnings = (application_id: string) => {
    // !! so we always return a Boolean
    return !!(
      warningsLists.hasOwnProperty(application_id) &&
      benefitsApplications.getItem(application_id)
    );
  };

  /**
   * Associate a claim created through the contact center with this user.
   */
  const associate = async (formState: { [key: string]: string }) => {
    appErrorsLogic.clearErrors();

    try {
      // TODO (PORTAL-1454) - Connect to the API endpoint
      await Promise.resolve();
    } catch (error) {
      // TODO (PORTAL-1454) - Add a test for this error handler once API endpoint is connected
      appErrorsLogic.catchError(error);
    }

    // Reset the applications pagination state to force applications to be refetched,
    // so that this newly associated application is listed
    setPaginationMeta({});

    portalFlow.goToNextPage(
      {},
      {
        applicationAssociated: formState.absence_id,
      }
    );
  };

  /**
   * Load a single claim
   */
  const load = async (application_id: string) => {
    // Skip API request if we already have the claim AND its validation warnings.
    // It's important we load the claim if warnings haven't been fetched yet,
    // since the Checklist needs those to be present in order to accurately
    // determine what steps are completed.
    if (hasLoadedBenefitsApplicationAndWarnings(application_id)) return;

    appErrorsLogic.clearErrors();

    try {
      const { claim, warnings } = await applicationsApi.getClaim(
        application_id
      );

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
   * Load a page of claims for the authenticated user
   * @param [pageOffset] - Page number to load
   */
  const loadPage = async (pageOffset: number | string = 1) => {
    if (isLoadingClaims) return;
    if (paginationMeta.page_offset === Number(pageOffset)) return;

    setIsLoadingClaims(true);
    appErrorsLogic.clearErrors();

    try {
      const { claims, paginationMeta } = await applicationsApi.getClaims(
        pageOffset
      );
      setBenefitsApplications(claims);
      setPaginationMeta(paginationMeta);
      setIsLoadingClaims(false);
    } catch (error) {
      appErrorsLogic.catchError(error);
      setIsLoadingClaims(false);
    }
  };

  /**
   * Update the claim in the API and set application errors if any
   * @param patchData - subset of claim data that will be updated, and
   * used as the list of fields to filter validation warnings by
   */
  const update = async (
    application_id: string,
    patchData: Partial<BenefitsApplication>
  ) => {
    appErrorsLogic.clearErrors();

    try {
      const { claim, warnings } = await applicationsApi.updateClaim(
        application_id,
        patchData
      );

      const issues = getRelevantIssues([], warnings, [portalFlow.page]);

      setBenefitsApplication(claim);
      setClaimWarnings(application_id, warnings);

      // If there were only validation warnings, then throw *after*
      // the claim has been updated in our state, so our local claim
      // state remains consistent with the claim state stored in the API,
      // which still received the updates in the request. This is important
      // for situations like leave periods, where the API passes us back
      // a leave_period_id field for making subsequent updates.
      if (issues.length) {
        throw new ValidationError(issues, applicationsApi.i18nPrefix);
      }

      const params = { claim_id: claim.application_id };
      portalFlow.goToNextPage({ claim }, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Complete the claim in the API
   */
  const complete = async (application_id: string) => {
    appErrorsLogic.clearErrors();

    try {
      const { claim } = await applicationsApi.completeClaim(application_id);

      setBenefitsApplication(claim);
      const context = { claim };
      const params = { claim_id: claim.application_id };
      portalFlow.goToNextPage(context, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Create the claim in the API. Handles errors and routing.
   */
  const create = async () => {
    appErrorsLogic.clearErrors();

    try {
      const { claim } = await applicationsApi.createClaim();

      addBenefitsApplication(claim);

      const context = { claim };
      const params = { claim_id: claim.application_id };
      portalFlow.goToPageFor("CREATE_CLAIM", context, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Submit the claim in the API and set application errors if any
   */
  const submit = async (application_id: string) => {
    appErrorsLogic.clearErrors();

    try {
      const { claim } = await applicationsApi.submitClaim(application_id);

      setBenefitsApplication(claim);

      const context = { claim };
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
    application_id: string,
    paymentPreferenceData: Partial<PaymentPreference>
  ) => {
    appErrorsLogic.clearErrors();

    try {
      const { claim, warnings } = await applicationsApi.submitPaymentPreference(
        application_id,
        paymentPreferenceData
      );

      // This endpoint should only return errors relevant to this page so no need to filter
      const issues = getRelevantIssues([], warnings, []);

      setBenefitsApplication(claim);
      setClaimWarnings(application_id, warnings);

      if (issues.length) {
        throw new ValidationError(issues, applicationsApi.i18nPrefix);
      }

      const context = { claim };
      const params: NullableQueryParams = {
        claim_id: claim.application_id,
        "payment-pref-submitted": "true",
      };

      portalFlow.goToNextPage(context, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  const submitTaxWithholdingPreference = async (
    application_id: string,
    data: TaxWithholdingPreference
  ) => {
    appErrorsLogic.clearErrors();

    try {
      const { claim, warnings } =
        await applicationsApi.submitTaxWithholdingPreference(
          application_id,
          data
        );

      setBenefitsApplication(claim);
      setClaimWarnings(application_id, warnings);

      const issues = getRelevantIssues([], warnings, []);
      if (issues.length) {
        throw new ValidationError(issues, applicationsApi.i18nPrefix);
      }

      const context = { claim };
      const params: NullableQueryParams = {
        claim_id: claim.application_id,
        "tax-pref-submitted": "true",
      };
      portalFlow.goToNextPage(context, params);
    } catch (err) {
      appErrorsLogic.catchError(err);
    }
  };

  return {
    associate,
    benefitsApplications,
    complete,
    create,
    hasLoadedBenefitsApplicationAndWarnings,
    isLoadingClaims,
    load,
    loadPage,
    paginationMeta,
    update,
    submit,
    submitPaymentPreference,
    submitTaxWithholdingPreference,
    warningsLists,
  };
};

export default useBenefitsApplicationsLogic;