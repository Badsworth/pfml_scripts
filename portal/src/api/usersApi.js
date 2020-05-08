/* eslint-disable jsdoc/require-returns */
import User from "../models/User";
import request from "./request";

/**
 * @typedef {{ apiErrors: object[], success: boolean, user: User }} UsersApiResult
 * @property {object[]} [apiErrors] - If the request failed, this will contain errors returned by the API
 * @property {number} status - Status code
 * @property {boolean} success - Did the request succeed or fail?
 * @property {User} [user] - If the request succeeded, this will contain the created user
 */

// Additional fields that would be returned by the API
const mockApiResponseFields = {
  status: "unverified",
  user_id: "009fa369-291b-403f-a85a-15e938c26f2f",
};

/**
 * Mock a POST /users request and return a "success" response
 * @param {User} user User properties
 * @returns {Promise<UsersApiResult>}
 */
async function createUser(user) {
  // todo: make a POST request to the api
  // Merge in additional fields that the API would populate
  const response = Object.assign({}, user, mockApiResponseFields);
  return Promise.resolve({
    success: true,
    user: new User(response),
  });
}

/**
 * Get the currently authenticated user
 * @returns {Promise<UsersApiResult>}
 */
async function getCurrentUser() {
  const { body, ...response } = await request("GET", "users/current");

  return Promise.resolve({
    ...response,
    user: response.success ? new User(body) : null,
  });
}

/**
 * Mock a PATCH /users request and return a "success" user response
 * Leaving this as a separate method in case we want to add some update
 * -specific behavior later
 * @todo Document the structure of error responses once we know what it looks like
 * @param {User} user User properties to update
 * @returns {Promise<UsersApiResult>}
 */
async function updateUser(user) {
  // todo: make a PATCH request to the api
  // const { body, success } = await request("PATCH", `users/${user.user_id}`, user);

  // Merge in additional fields that the API would populate
  const response = Object.assign({}, user, mockApiResponseFields);
  return Promise.resolve({
    success: true,
    user: new User(response),
  });
}

export default {
  createUser,
  getCurrentUser,
  updateUser,
};
