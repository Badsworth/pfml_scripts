/* eslint-disable jsdoc/require-returns */
import BaseApi from "./BaseApi";
import User from "../models/User";
import routes from "../routes";

/**
 * @typedef {{ success: boolean, user: User }} UsersApiResult
 * @property {number} status - Status code
 * @property {boolean} success - Did the request succeed or fail?
 * @property {User} [user] - If the request succeeded, this will contain the created user
 */

export default class UsersApi extends BaseApi {
  get basePath() {
    return routes.api.users;
  }

  get i18nPrefix() {
    return "users";
  }

  /**
   * Get the currently authenticated user
   * @returns {Promise<UsersApiResult>}
   */
  getCurrentUser = async () => {
    const { data, success, status } = await this.request(
      "GET",
      "current",
      null
    );

    return Promise.resolve({
      success,
      status,
      user: success ? new User(data) : null,
    });
  };

  /**
   * Update a user
   * @param {object} user_id - ID of user being updated
   * @param {object} patchData - User fields to update
   * @returns {Promise<UsersApiResult>}
   */
  updateUser = async (user_id, patchData) => {
    const { data, success, status } = await this.request(
      "PATCH",
      user_id,
      patchData
    );

    return {
      success,
      status,
      user: success ? new User({ ...patchData, ...data }) : null,
    };
  };
}
