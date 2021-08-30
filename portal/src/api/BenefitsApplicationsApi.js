/* eslint-disable jsdoc/require-returns */
import BaseApi from "./BaseApi";
import BenefitsApplication from "../models/BenefitsApplication";
import BenefitsApplicationCollection from "../models/BenefitsApplicationCollection";
import routes from "../routes";

/**
 * @typedef {object} BenefitsApplicationsApiSingleResult
 * @property {BenefitsApplication} [claim] - If the request succeeded, this will contain the created claim
 * @property {{ field: string, message: string, rule: string, type: string }[]} [warnings] - Validation warnings
 */

/**
 * @typedef {object} BenefitsApplicationsApiListResult
 * @property {BenefitsApplicationCollection} [claims] - If the request succeeded, this will contain the created user
 */

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
   * @private
   * @returns {object}
   */
  get featureFlagHeaders() {
    const headers = {};

    // Add any feature flag headers here. eg:
    // if (isFeatureEnabled("claimantShowOtherLeaveStep")) {
    //   headers["X-FF-Require-Other-Leaves"] = true;
    // }

    return headers;
  }

  /**
   * Send an authenticated API request, with feature flag headers
   * @example const response = await this.request("GET", "users/current");
   *
   * @param {string} method - i.e GET, POST, etc
   * @param {string} subPath - relative path without a leading forward slash
   * @param {object|FormData} [body] - request body
   * @returns {Promise<{ data: object, warnings?: object[]}>} response - rejects on non-2xx status codes
   */
  request(method, subPath, body) {
    return super.request(method, subPath, body, this.featureFlagHeaders);
  }

  /**
   * Fetches a single claim
   * @returns {Promise<BenefitsApplicationsApiSingleResult>} The result of the API call
   */
  getClaim = async (application_id) => {
    const { data, warnings } = await this.request("GET", application_id);

    return {
      claim: new BenefitsApplication(data),
      warnings,
    };
  };

  /**
   * Fetches the list of claims for a user
   * @returns {Promise<BenefitsApplicationsApiListResult>} The result of the API call
   */
  getClaims = async () => {
    const { data } = await this.request("GET");

    let claims = data.map((claimData) => new BenefitsApplication(claimData));
    claims = new BenefitsApplicationCollection(claims);

    return {
      claims,
    };
  };

  /**
   * Signal the data entry is complete and application is ready
   * for intake to be marked as complete in the claims processing system.
   *
   * @param {string} application_id
   * @returns {Promise<BenefitsApplicationsApiSingleResult>} The result of the API call
   */
  completeClaim = async (application_id) => {
    const { data } = await this.request(
      "POST",
      `${application_id}/complete_application`
    );

    return {
      claim: new BenefitsApplication(data),
    };
  };

  /**
   * Create a new claim through a POST request to /applications
   * @returns {Promise<BenefitsApplicationsApiSingleResult>} The result of the API call
   */
  createClaim = async () => {
    const { data } = await this.request("POST");

    return {
      claim: new BenefitsApplication(data),
    };
  };

  /**
   * Update claim through a PATCH request to /applications.
   * @param {string} application_id ID of the Claim
   * @param {object} patchData Claim fields to update
   * @returns {Promise<BenefitsApplicationsApiSingleResult>} The result of the API call
   */
  updateClaim = async (application_id, patchData) => {
    const { data, errors, warnings } = await this.request(
      "PATCH",
      application_id,
      patchData
    );

    return {
      claim: new BenefitsApplication(data),
      errors,
      warnings,
    };
  };

  /**
   * Signal data entry for Part 1 is complete and ready
   * to be submitted to the claims processing system.
   *
   * @param {string} application_id ID of the Claim
   * @returns {Promise<BenefitsApplicationsApiSingleResult>} The result of the API call
   */
  submitClaim = async (application_id) => {
    const { data } = await this.request(
      "POST",
      `${application_id}/submit_application`
    );

    return {
      claim: new BenefitsApplication(data),
    };
  };

  submitPaymentPreference = async (application_id, paymentPreferenceData) => {
    const { data, errors, warnings } = await this.request(
      "POST",
      `${application_id}/submit_payment_preference`,
      paymentPreferenceData
    );

    return {
      claim: new BenefitsApplication(data),
      errors,
      warnings,
    };
  };
}
