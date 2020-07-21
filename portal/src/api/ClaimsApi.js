/* eslint-disable jsdoc/require-returns */
import Claim from "../models/Claim";
import ClaimCollection from "../models/ClaimCollection";
import merge from "lodash/merge";
import portalRequest from "./portalRequest";
import routes from "../routes";

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
   * @param {string} [subPath] Sub-path of the /applications resource to use
   * @param {object} [body] Request body
   * @param {object} [additionalHeaders] Additional headers to add to the request
   */
  claimsRequest = async (
    method,
    subPath = "",
    body = null,
    additionalHeaders = {}
  ) => {
    const apiPath = `${routes.api.claims}${subPath}`;
    const baseHeaders = { user_id: this.user.user_id };
    const headers = {
      ...baseHeaders,
      ...additionalHeaders,
    };

    return portalRequest(method, apiPath, body, headers);
  };

  /**
   * Fetches the list of claims for a user
   * @returns {Promise<ClaimsApiListResult>} The result of the API call
   */
  getClaims = async () => {
    const { body, success, status, apiErrors } = await this.claimsRequest(
      "GET"
    );

    let claims = null;
    if (success) {
      claims = body.map((claimData) => new Claim(claimData));
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
    // TODO (CP-716): Send SSN in the API payload once production can accept PII
    const { employee_ssn, ...workaroundPatchData } = patchData;

    const { body, success, status, apiErrors } = await this.claimsRequest(
      "PATCH",
      `/${application_id}`,
      workaroundPatchData
    );

    // Currently the API doesn't return the claim data in the response
    // so we're manually constructing the body based on client data.
    // We will change the PATCH applications endpoint to return the full
    // application in this ticket: https://lwd.atlassian.net/browse/API-276
    // TODO: Remove workaround once above ticket is complete: https://lwd.atlassian.net/browse/CP-577
    const workaroundBody = merge({ ...body, application_id }, patchData);
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
   * to be submitted to the claims processing system.
   *
   * Corresponds to this API endpoint: /application/{application_id}/submit_application
   * @todo Document the possible errors
   * @param {string} application_id ID of the Claim
   * @returns {Promise<ClaimsApiSingleResult>} The result of the API call
   */
  submitClaim = async (application_id) => {
    const { body, status, success, apiErrors } = await this.claimsRequest(
      "POST",
      `/${application_id}/submit_application`
    );

    // Currently the API doesn't return the claim data in the response.
    // We will change the PATCH applications endpoint to return the full
    // application in this ticket: https://lwd.atlassian.net/browse/API-276
    // TODO: Remove workaround once above ticket is complete: https://lwd.atlassian.net/browse/CP-577
    const workaroundBody = { ...body, application_id };
    // </ end workaround >

    return {
      apiErrors,
      claim: success ? new Claim(workaroundBody) : null,
      status,
      success,
    };
  };
}
