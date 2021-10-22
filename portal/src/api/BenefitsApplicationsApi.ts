import BaseApi, { ApiMethod, ApiRequestBody } from "./BaseApi";
import BenefitsApplication from "../models/BenefitsApplication";
import BenefitsApplicationCollection from "../models/BenefitsApplicationCollection";
import PaymentPreference from "../models/PaymentPreference";
import routes from "../routes";

export default class BenefitsApplicationsApi extends BaseApi {
  get basePath() {
    return routes.api.applications;
  }

  get i18nPrefix() {
    return "applications";
  }

  /**
   * Pass feature flags to the API as headers to enable
   * API functionality that can be toggled on/off.
   */
  private get featureFlagHeaders() {
    const headers = {};

    // Add any feature flag headers here. eg:
    // if (isFeatureEnabled("claimantShowOtherLeaveStep")) {
    //   headers["X-FF-Require-Other-Leaves"] = true;
    // }

    return headers;
  }

  /**
   * Send an authenticated API request, with feature flag headers
   */
  request<TResponseData>(
    method: ApiMethod,
    subPath?: string,
    body?: ApiRequestBody
  ) {
    return super.request<TResponseData>(
      method,
      subPath,
      body,
      this.featureFlagHeaders
    );
  }

  getClaim = async (application_id: string) => {
    const { data, warnings } = await this.request<BenefitsApplication>(
      "GET",
      application_id
    );

    return {
      claim: new BenefitsApplication(data),
      warnings,
    };
  };

  /**
   * Fetches the list of claims for a user
   */
  getClaims = async () => {
    const { data } = await this.request<BenefitsApplication[]>("GET");

    const claims = data.map((claimData) => new BenefitsApplication(claimData));

    return {
      claims: new BenefitsApplicationCollection(claims),
    };
  };

  /**
   * Signal the data entry is complete and application is ready
   * for intake to be marked as complete in the claims processing system.
   */
  completeClaim = async (application_id: string) => {
    const { data } = await this.request<BenefitsApplication>(
      "POST",
      `${application_id}/complete_application`
    );

    return {
      claim: new BenefitsApplication(data),
    };
  };

  createClaim = async () => {
    const { data } = await this.request<BenefitsApplication>("POST");

    return {
      claim: new BenefitsApplication(data),
    };
  };

  updateClaim = async (
    application_id: string,
    patchData: Partial<BenefitsApplication>
  ) => {
    const { data, warnings } = await this.request<BenefitsApplication>(
      "PATCH",
      application_id,
      patchData
    );

    return {
      claim: new BenefitsApplication(data),
      warnings,
    };
  };

  /**
   * Signal data entry for Part 1 is complete and ready
   * to be submitted to the claims processing system.
   */
  submitClaim = async (application_id: string) => {
    const { data } = await this.request<BenefitsApplication>(
      "POST",
      `${application_id}/submit_application`
    );

    return {
      claim: new BenefitsApplication(data),
    };
  };

  submitPaymentPreference = async (
    application_id: string,
    paymentPreferenceData: Partial<PaymentPreference>
  ) => {
    const { data, warnings } = await this.request<BenefitsApplication>(
      "POST",
      `${application_id}/submit_payment_preference`,
      paymentPreferenceData
    );

    return {
      claim: new BenefitsApplication(data),
      warnings,
    };
  };
}
