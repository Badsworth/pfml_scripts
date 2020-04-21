/* eslint-disable jsdoc/require-returns */

// Additional fields that would be returned by the API
const apiResponseFields = {
  status: "unverified",
  user_id: "009fa369-291b-403f-a85a-15e938c26f2f",
};

/**
 * User object returned by the API
 * @todo Update this structure once we have integrated with the API
 * @typedef User
 * @property {string} email User's email address
 * @property {string} status Identity proofing status
 * @property {string} userId User's ID
 * @property {string} firstName First name
 * @property {string} middleName Middle name
 * @property {string} lastName Last name
 * @property {string} dateOfBirth Date of birth string in ISO-8601 format
 * @property {string} ssnOrItin User's SSN or ITIN
 */

/**
 * Mock a POST /users request and return a "success" response
 * @todo Document the structure of error responses once we know what it looks like
 * @param {User} user User properties
 * @returns {object} result The result of the API call
 * @returns {boolean} result.success Did the call succeed or fail?
 * @returns {User} result.user If result.success === true this will contain the created user
 * @returns {Array} result.errors If result.success === false this will contain errors returned by the API
 */
async function createUser(user) {
  // todo: make a POST request to the api
  // Merge in additional fields that the API would populate
  const response = Object.assign({}, apiResponseFields, user);
  return Promise.resolve({
    success: true,
    user: response,
  });
}

/**
 * Mock a PATCH /users request and return a "success" user response
 * Leaving this as a separate method in case we want to add some update
 * -specific behavior later
 * @todo Document the structure of error responses once we know what it looks like
 * @param {User} user User properties to update
 * @returns {object} result The result of the API call
 * @returns {boolean} result.success Did the call succeed or fail?
 * @returns {User} result.user If result.success === true this will contain the updated user
 * @returns {Array} result.errors If result.success === false this will contain errors returned by the API
 */
async function updateUser(user) {
  // todo: make a PATCH request to the api
  // Merge in additional fields that the API would populate
  const response = Object.assign({}, apiResponseFields, user);
  return Promise.resolve({
    success: true,
    user: response,
  });
}

export default {
  createUser,
  updateUser,
};
