/* eslint-disable jsdoc/require-returns */
import Claim from "../models/Claim";
import Collection from "../models/Collection";
import request from "./request";
import routes from "../routes";

const apiResponseFields = {
  success: true,
  status: 201,
  apiErrors: [],
};

/**
 * @typedef {{ apiErrors: object[], success: boolean, claim: Claim }} ClaimsApiSingleResult
 * @property {object[]} [apiErrors] - If the request failed, this will contain errors returned by the API
 * @property {number} status - Status code
 * @property {boolean} success - Did the request succeed or fail?
 * @property {Claim} [claim] - If the request succeeded, this will contain the created claim
 */

/**
 * @typedef {{ apiErrors: object[], success: boolean, claims: Collection }} ClaimsApiListResult
 * @property {object[]} [apiErrors] - If the request failed, this will contain errors returned by the API
 * @property {number} status - Status code
 * @property {boolean} success - Did the request succeed or fail?
 * @property {Collection} [claims] - If the request succeeded, this will contain the created user
 */

export default class ClaimsApi {
  constructor({ user }) {
    if (!user) {
      throw new Error("ClaimsApi expects an instance of a user.");
    }

    this.user = user;
  }

  /**
   * Private method used by other methods in this class to make REST API requests
   * related to the /applications resource.
   * @private
   * @param {string} method HTTP method
   * @param {object} body Request body
   * @param {string} application_id ID of the claim
   * @param {object} additionalHeaders Additional headers to add to the request
   */
  claimsRequest = async (
    method,
    body = null,
    application_id = null,
    additionalHeaders = {}
  ) => {
    const apiPath = application_id
      ? `${routes.api.claims}/${application_id}`
      : routes.api.claims;
    const baseHeaders = { user_id: this.user.user_id };
    const headers = {
      ...baseHeaders,
      ...additionalHeaders,
    };
    return request(method, apiPath, body, headers);
  };

  /**
   * Fetches the list of claims for a user
   * @param {string} user_id The user's user id
   * @returns {Promise<ClaimsApiListResult>} The result of the API call
   */
  getClaims = async (user_id) => {
    const { body, success, status, apiErrors } = await this.claimsRequest(
      "GET"
    );

    let claims = null;
    if (success) {
      const itemsById = {};
      for (const claimData of body) {
        itemsById[claimData.application_id] = new Claim(claimData);
      }
      claims = new Collection({ idProperty: "application_id", itemsById });
    }

    return {
      success,
      status,
      apiErrors,
      claims,
    };
  };

  /**
   * Create a new claim through a POST request to /applications
   * @todo Document the structure of error responses once we know what it looks like
   * @param {Claim} claim Claim properties
   * @returns {Promise<ClaimsApiSingleResult>} The result of the API call
   */
  createClaim = async (claim) => {
    const { body, success, status, apiErrors } = await this.claimsRequest(
      "POST",
      claim
    );

    return {
      success,
      status,
      apiErrors,
      claim: success ? new Claim(body) : null,
    };
  };

  /**
   * Update claim through a PATCH request to /applications.
   * @param {string} application_id ID of the Claim
   * @param {object} patchData Claim fields to update
   * @returns {Promise<ClaimsApiSingleResult>} The result of the API call
   */
  updateClaim = async (application_id, patchData) => {
    // The API currently returns 500 errors if some fields are missing, so we need to always pass
    // certain fields in the API request.
    // See https://lwd.atlassian.net/browse/API-259, https://lwd.atlassian.net/browse/API-260, https://lwd.atlassian.net/browse/API-263
    // TODO: Remove this workaround
    const workaroundDefaultsForAPI = {
      leave_details: {
        continuous_leave_periods: [{ status: "Estimated" }],
      },
      payment_preferences: [{ description: "Test" }],
    };
    patchData = {
      ...workaroundDefaultsForAPI,
      ...patchData,
    };

    const { body, success, status, apiErrors } = await this.claimsRequest(
      "PATCH",
      patchData,
      application_id
    );

    return {
      success,
      status,
      apiErrors,
      claim: success ? new Claim(body) : null,
    };
  };

  /**
   * Signal the data entry is complete and application is ready
   * to be submitted to the payment processor.
   *
   * Corresponds to this API endpoint: /application/{application_id}/submit_application
   * @todo Document the possible errors
   * @todo This is a mock -- connect to the actual API when ready
   * @param {Claim} claim Claim properties
   * @returns {Promise<ClaimsApiSingleResult>} The result of the API call
   */
  submitClaim = async (claim) => {
    const { body, status, success, apiErrors } = Object.assign(
      {},
      { body: claim },
      apiResponseFields
    );
    return Promise.resolve({
      success,
      status,
      claim: new Claim(body),
      apiErrors,
    });
  };
}
