/* eslint-disable jsdoc/require-returns */
import User from "../models/User";
import request from "./request";

// TODO: Convert userApi to class like ClaimsApi

/**
 * @typedef {{ apiErrors: object[], success: boolean, user: User }} UsersApiResult
 * @property {object[]} [apiErrors] - If the request failed, this will contain errors returned by the API
 * @property {number} status - Status code
 * @property {boolean} success - Did the request succeed or fail?
 * @property {User} [user] - If the request succeeded, this will contain the created user
 */

/**
 * Get the currently authenticated user
 * @returns {Promise<UsersApiResult>}
 */
async function getCurrentUser() {
  // TODO: add api route to routes file and reference routes.api.currentUser
  const { body, ...response } = await request("GET", "users/current");

  return Promise.resolve({
    ...response,
    user: response.success ? new User(body) : null,
  });
}

/**
 * Update a user
 * @param {object} user_id - ID of user being updated
 * @param {object} patchData - User fields to update
 * @returns {Promise<UsersApiResult>}
 */
async function updateUser(user_id, patchData) {
  const { body, success, status, apiErrors } = await request(
    "PATCH",
    `users/${user_id}`,
    patchData
  );

  return {
    success,
    status,
    apiErrors,
    user: success ? new User(body) : null,
  };
}

export default {
  getCurrentUser,
  updateUser,
};
