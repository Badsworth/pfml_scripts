/* eslint-disable jsdoc/require-returns */
import BaseApi from "./BaseApi";
import Claim from "../models/Claim";
import ClaimCollection from "../models/ClaimCollection";
import { isFeatureEnabled } from "../services/featureFlags";
import routes from "../routes";

/**
 * @typedef {object} ClaimsApiSingleResult
 * @property {Claim} [claim] - If the request succeeded, this will contain the created claim
 * @property {{ field: string, message: string, rule: string, type: string }[]} [warnings] - Validation warnings
 */

/**
 * @typedef {object} ClaimsApiListResult
 * @property {ClaimCollection} [claims] - If the request succeeded, this will contain the created user
 */

export default class ClaimsApi extends BaseApi {
  get basePath() {
    return routes.api.claims;
  }

  get i18nPrefix() {
    return "claims";
  }

  /**
   * Pass feature flags to the API as headers to enable
   * API functionality that can be toggled on/off.
   * @private
   * @returns {object}
   */
  get featureFlagHeaders() {
    const headers = {};

    if (isFeatureEnabled("claimantShowOtherLeaveStep")) {
      // Enable validation on fields in the Other Leave step
      headers["X-FF-Require-Other-Leaves"] = true;
    }

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
   * @returns {Promise<ClaimsApiSingleResult>} The result of the API call
   */
  getClaim = async (application_id) => {
    const { data, warnings } = await this.request("GET", application_id);

    return {
      claim: new Claim(data),
      warnings,
    };
  };

  /**
   * Fetches the list of claims for a user
   * @returns {Promise<ClaimsApiListResult>} The result of the API call
   */
  getClaims = async () => {
    const { data } = await this.request("GET");

    let claims = data.map((claimData) => new Claim(claimData));
    claims = new ClaimCollection(claims);

    return {
      claims,
    };
  };

  /**
   * Signal the data entry is complete and application is ready
   * for intake to be marked as complete in the claims processing system.
   *
   * @param {string} application_id
   * @returns {Promise<ClaimsApiSingleResult>} The result of the API call
   */
  completeClaim = async (application_id) => {
    const { data } = await this.request(
      "POST",
      `${application_id}/complete_application`
    );

    return {
      claim: new Claim(data),
    };
  };

  /**
   * Create a new claim through a POST request to /applications
   * @returns {Promise<ClaimsApiSingleResult>} The result of the API call
   */
  createClaim = async () => {
    const { data } = await this.request("POST");

    return {
      claim: new Claim(data),
    };
  };

  /**
   * Update claim through a PATCH request to /applications.
   * @param {string} application_id ID of the Claim
   * @param {object} patchData Claim fields to update
   * @returns {Promise<ClaimsApiSingleResult>} The result of the API call
   */
  updateClaim = async (application_id, patchData) => {
    const { data, errors, warnings } = await this.request(
      "PATCH",
      application_id,
      patchData
    );

    return {
      claim: new Claim(data),
      errors,
      warnings,
    };
  };

  /**
   * Signal data entry for Part 1 is complete and ready
   * to be submitted to the claims processing system.
   *
   * @param {string} application_id ID of the Claim
   * @returns {Promise<ClaimsApiSingleResult>} The result of the API call
   */
  submitClaim = async (application_id) => {
    const { data } = await this.request(
      "POST",
      `${application_id}/submit_application`
    );

    return {
      claim: new Claim(data),
    };
  };

  submitPaymentPreference = async (application_id, paymentPreferenceData) => {
    const { data, errors, warnings } = await this.request(
      "POST",
      `${application_id}/submit_payment_preference`,
      paymentPreferenceData
    );

    return {
      claim: new Claim(data),
      errors,
      warnings,
    };
  };
}
