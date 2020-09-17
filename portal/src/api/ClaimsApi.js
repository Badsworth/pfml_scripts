/* eslint-disable jsdoc/require-returns */
import BaseApi from "./BaseApi";
import Claim from "../models/Claim";
import ClaimCollection from "../models/ClaimCollection";
import { isFeatureEnabled } from "../services/featureFlags";
import merge from "lodash/merge";
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

export default class ClaimsApi extends BaseApi {
  get basePath() {
    return routes.api.claims;
  }

  /**
   * Fetches the list of claims for a user
   * @returns {Promise<ClaimsApiListResult>} The result of the API call
   */
  getClaims = async () => {
    const { data, success, status } = await this.request("GET");

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
   * Signal the data entry is complete and application is ready
   * for intake to be marked as complete in the claims processing system.
   *
   * @param {string} application_id
   * @returns {Promise<ClaimsApiSingleResult>} The result of the API call
   */
  completeClaim = async (application_id) => {
    const { data, status, success } = await this.request(
      "POST",
      `${application_id}/complete_application`
    );

    return {
      claim: success ? new Claim(data) : null,
      status,
      success,
    };
  };

  /**
   * Create a new claim through a POST request to /applications
   * @returns {Promise<ClaimsApiSingleResult>} The result of the API call
   */
  createClaim = async () => {
    const { data, success, status } = await this.request("POST");

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
    const { tax_identifier, ...patchDataWithoutExcludedPii } = patchData;
    const requestData = isFeatureEnabled("sendPii")
      ? patchData
      : patchDataWithoutExcludedPii;

    const { data, errors, success, status, warnings } = await this.request(
      "PATCH",
      application_id,
      requestData,
      {
        "X-PFML-Warn-On-Missing-Required-Fields": true,
      }
    );

    // TODO (CP-676): Remove workaround once API returns all the fields in our application
    const workaroundData = merge({ ...data, application_id }, patchData);
    // </ end workaround >

    return {
      claim: success ? new Claim(workaroundData) : null,
      errors,
      success,
      status,
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
    const { data, status, success } = await this.request(
      "POST",
      `${application_id}/submit_application`
    );

    // TODO (CP-676): Remove workaround once API returns all the fields in our application
    const workaroundData = { ...data, application_id };
    // </ end workaround >

    return {
      claim: success ? new Claim(workaroundData) : null,
      status,
      success,
    };
  };

  /**
   * Submit documents one at a time
   *
   * Corresponds to this API endpoint: /application/{application_id}/documents
   * @param {string} application_id ID of the Claim
   * @param {FileList} files FileList object, an iterable collection of File objects
   * @param {string} documentCategory category of documents
   * @returns {Promise<ClaimsApiSingleResult>} The result of the API call
   */
  attachDocuments = async (application_id, files, documentCategory) => {
    const formData = new FormData();
    // TODO (CP-993): handle multiple file uploads
    const file = files[0];
    // TODO (CP-962): set document_category and document_type based on leave reason
    formData.append("description", "testDescription");
    formData.append("document_category", "Certification");
    formData.append("document_type", "Passport");
    formData.append("file", file.file);
    formData.append("name", file.file.name);

    const { status, success } = await this.request(
      "POST",
      `${application_id}/documents`,
      formData,
      null,
      { multipartForm: true }
    );

    // TODO (CP-959): Update document store on successful response

    return {
      status,
      success,
    };
  };
}
