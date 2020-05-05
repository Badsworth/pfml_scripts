/* eslint-disable jsdoc/require-returns */
import Claim from "../models/Claim";
import uuid from "../utils/uuid";

const apiResponseFields = {};

/**
 * Mock a POST /users request and return a "success" response
 * @todo Document the structure of error responses once we know what it looks like
 * @param {Claim} claim Claim properties
 * @returns {object} result The result of the API call
 * @returns {boolean} result.success Did the call succeed or fail?
 * @returns {Claim} result.claim If result.success === true this will contain the created user
 * @returns {Array} result.errors If result.success === false this will contain errors returned by the API
 */
async function createClaim(claim) {
  // todo: make a POST request to the api
  // Merge in additional fields that the API would populate
  const response = Object.assign(
    { claim_id: uuid() },
    claim,
    apiResponseFields
  );
  return Promise.resolve({
    success: true,
    claim: new Claim(response),
  });
}

async function updateClaim(claim) {
  const response = Object.assign({}, claim, apiResponseFields);
  return Promise.resolve({
    success: true,
    claim: new Claim(response),
  });
}

export default {
  createClaim,
  updateClaim,
};
