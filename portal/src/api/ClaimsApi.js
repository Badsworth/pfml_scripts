/* eslint-disable jsdoc/require-returns */
import Claim from "../models/Claim";
import request from "./request";
import routes from "../routes";

const apiResponseFields = {};

export default class ClaimsApi {
  constructor({ user }) {
    if (!user) {
      throw new Error("ClaimsApi expects an instance of a user.");
    }

    this.user = user;
    this.baseRoute = routes.api.claims;
  }

  /**
   * get headers common to all requests
   * @param {object} additionalHeaders - add additional headers
   * @returns {object} headers
   */
  headers = (additionalHeaders = {}) => {
    return {
      user_id: this.user.user_id,
      ...additionalHeaders,
    };
  };

  /**
   * Create a new claim through a POST request to /applications
   * @todo Document the structure of error responses once we know what it looks like
   * @param {Claim} claim Claim properties
   * @returns {object} result The result of the API call
   * @returns {boolean} result.success Did the call succeed or fail?
   * @returns {string} result.status Server response status code
   * @returns {Claim} result.claim If result.success === true this will contain the created claim
   * @returns {Array} result.apiErrors If result.success === false this will contain errors returned by the API
   */
  createClaim = async (claim) => {
    const { body, success, status, apiErrors } = await request(
      "POST",
      this.baseRoute,
      claim,
      this.headers()
    );

    return {
      success,
      status,
      apiErrors,
      claim: success ? new Claim(body) : null,
    };
  };

  updateClaim = async (claim) => {
    const response = Object.assign({}, claim, apiResponseFields);
    return Promise.resolve({
      success: true,
      claim: new Claim(response),
    });
  };

  /**
   * Signal the data entry is complete and application is ready
   * to be submitted to the payment processor.
   *
   * Corresponds to this API endpoint: /application/{application_id}/submit_application
   * @todo Document the possible errors
   * @todo This is a mock -- connect to the actual API when ready
   * @param {Claim} claim claim properties
   * @returns {object} result The result of the API call
   * @returns {boolean} result.success Did the call succeed?
   * @returns {string} result.status Server response status code
   * @returns {Claim} result.claim If result.success === true this will contain the submitted claim information
   * @returns {Array} result.apiErrors if result.success === false this will contain errors returned by the API
   */
  submitClaim = async (claim) => {
    const response = Object.assign({}, claim, apiResponseFields);
    return Promise.resolve({
      success: true,
      status: "201",
      claim: new Claim(response),
      apiErrors: [],
    });
  };
}
