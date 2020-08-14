/* eslint-disable jsdoc/require-returns */
import Claim from "../models/Claim";
import ClaimCollection from "../models/ClaimCollection";
import { isFeatureEnabled } from "../services/featureFlags";
import merge from "lodash/merge";
import portalRequest from "./portalRequest";
import routes from "../routes";

/**
 * @typedef {{ success: boolean, claim: Claim }} ClaimsApiSingleResult
 * @property {number} status - Status code
 * @property {boolean} success - Did the request succeed or fail?
 * @property {Claim} [claim] - If the request succeeded, this will contain the created claim
 */

/**
 * @typedef {{ success: boolean, claims: ClaimCollection }} ClaimsApiListResult
 * @property {number} status - Status code
 * @property {boolean} success - Did the request succeed or fail?
 * @property {ClaimCollection} [claims] - If the request succeeded, this will contain the created user
 */

export default class ClaimsApi {
  /**
   * Private method used by other methods in this class to make REST API requests
   * related to the /applications resource.
   * @private
   * @param {string} method HTTP method
   * @param {string} [subPath] Sub-path of the /applications resource to use
   * @param {object} [body] Request body
   */
  claimsRequest = async (method, subPath = "", body = null) => {
    const apiPath = `${routes.api.claims}${subPath}`;
    return portalRequest(method, apiPath, body);
  };

  /**
   * Fetches the list of claims for a user
   * @returns {Promise<ClaimsApiListResult>} The result of the API call
   */
  getClaims = async () => {
    const { data, success, status } = await this.claimsRequest("GET");

    let claims = null;
    if (success) {
      claims = data.map((claimData) => new Claim(claimData));
      claims = new ClaimCollection(claims);
    }

    return {
      success,
      status,
      claims,
    };
  };

  /**
   * Create a new claim through a POST request to /applications
   * @todo Document the structure of error responses once we know what it looks like
   * @returns {Promise<ClaimsApiSingleResult>} The result of the API call
   */
  createClaim = async () => {
    const { data, success, status } = await this.claimsRequest("POST");

    return {
      success,
      status,
      claim: success ? new Claim(data) : null,
    };
  };

  /**
   * Update claim through a PATCH request to /applications.
   * @param {string} application_id ID of the Claim
   * @param {object} patchData Claim fields to update
   * @returns {Promise<ClaimsApiSingleResult>} The result of the API call
   */
  updateClaim = async (application_id, patchData) => {
    // TODO (CP-716): Send SSN in the API payload once production can accept PII
    const { employee_ssn, ...patchDataWithoutExcludedPii } = patchData;
    const requestData = isFeatureEnabled("sendPii")
      ? patchData
      : patchDataWithoutExcludedPii;

    const { data, success, status } = await this.claimsRequest(
      "PATCH",
      `/${application_id}`,
      requestData
    );

    // Currently the API doesn't return the claim data in the response
    // so we're manually constructing the body based on client data.
    // We will change the PATCH applications endpoint to return the full
    // application in this ticket: https://lwd.atlassian.net/browse/API-276
    // TODO: Remove workaround once above ticket is complete: https://lwd.atlassian.net/browse/CP-577
    const workaroundData = merge({ ...data, application_id }, patchData);
    // </ end workaround >

    return {
      success,
      status,
      claim: success ? new Claim(workaroundData) : null,
    };
  };

  /**
   * Signal the data entry is complete and application is ready
   * to be submitted to the claims processing system.
   *
   * Corresponds to this API endpoint: /application/{application_id}/submit_application
   * @todo Document the possible errors
   * @param {string} application_id ID of the Claim
   * @returns {Promise<ClaimsApiSingleResult>} The result of the API call
   */
  submitClaim = async (application_id) => {
    const { data, status, success } = await this.claimsRequest(
      "POST",
      `/${application_id}/submit_application`
    );

    // Currently the API doesn't return the claim data in the response.
    // We will change the PATCH applications endpoint to return the full
    // application in this ticket: https://lwd.atlassian.net/browse/API-276
    // TODO: Remove workaround once above ticket is complete: https://lwd.atlassian.net/browse/CP-577
    const workaroundData = { ...data, application_id };
    // </ end workaround >

    return {
      claim: success ? new Claim(workaroundData) : null,
      status,
      success,
    };
  };
}
