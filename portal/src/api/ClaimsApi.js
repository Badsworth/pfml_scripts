/* eslint-disable jsdoc/require-returns */
import Claim from "../models/Claim";
import ClaimCollection from "../models/ClaimCollection";
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
 * @typedef {{ apiErrors: object[], success: boolean, claims: ClaimCollection }} ClaimsApiListResult
 * @property {object[]} [apiErrors] - If the request failed, this will contain errors returned by the API
 * @property {number} status - Status code
 * @property {boolean} success - Did the request succeed or fail?
 * @property {ClaimCollection} [claims] - If the request succeeded, this will contain the created user
 */

export default class ClaimsApi {
  constructor({ user }) {
    // if (!user) {
    //   throw new Error("ClaimsApi expects an instance of a user.");
    // }

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
      claims = body.map((claimData) => new Claim(claimData));

      // Workaround since GET /applications currently doesn't return the full
      // application body, so we need to call GET /application/[app id] for each
      // application.
      // We will change the GET /applications endpoint to return full applications
      // in this ticket https://lwd.atlassian.net/browse/API-290
      // TODO: Remove workaround once above ticket is complete: https://lwd.atlassian.net/browse/CP-577
      const application_ids = body.map((claimData) => claimData.application_id);
      const fullResponses = await Promise.all(
        application_ids.map((application_id) =>
          this.claimsRequest("GET", null, application_id)
        )
      );
      claims = fullResponses.map(
        (fullResponse) => new Claim(fullResponse.body)
      );
      // end workaround

      claims = new ClaimCollection(claims);
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
   * @returns {Promise<ClaimsApiSingleResult>} The result of the API call
   */
  createClaim = async () => {
    const { body, success, status, apiErrors } = await this.claimsRequest(
      "POST"
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
    const { body, success, status, apiErrors } = await this.claimsRequest(
      "PATCH",
      patchData,
      application_id
    );

    // Currently the API doesn't return the claim data in the response
    // so we're manually constructing the body based on client data.
    // We will change the PATCH applications endpoint to return the full
    // application in this ticket: https://lwd.atlassian.net/browse/API-247
    // TODO: Remove workaround once above ticket is complete: https://lwd.atlassian.net/browse/CP-577
    const workaroundBody = { ...body, ...patchData, application_id };
    // </ end workaround >

    return {
      success,
      status,
      apiErrors,
      claim: success ? new Claim(workaroundBody) : null,
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
