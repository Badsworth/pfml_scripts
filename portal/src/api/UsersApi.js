/* eslint-disable jsdoc/require-returns */
import User from "../models/User";
import portalRequest from "./portalRequest";
import routes from "../routes";

/**
 * @typedef {{ success: boolean, user: User }} UsersApiResult
 * @property {number} status - Status code
 * @property {boolean} success - Did the request succeed or fail?
 * @property {User} [user] - If the request succeeded, this will contain the created user
 */

export default class UsersApi {
  get baseRoute() {
    return routes.api.users;
  }

  /**
   * Get the currently authenticated user
   * @returns {Promise<UsersApiResult>}
   */
  getCurrentUser = async () => {
    const { data, success, status } = await portalRequest(
      "GET",
      `${this.baseRoute}/current`,
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
    // API does not accept these fields yet
    // TODO remove once API accepts these fields
    const {
      has_state_id,
      status: stat,
      state_id,
      email_address,
      user_id: userId,
      date_of_birth,
      auth_id,
      ...workaroundPatchData
    } = patchData;

    const { data, success, status } = await portalRequest(
      "PATCH",
      `${this.baseRoute}/${user_id}`,
      workaroundPatchData
    );

    return {
      success,
      status,
      user: success ? new User({ ...patchData, ...data }) : null,
    };
  };
}
