import BaseApi from "./BaseApi";
import User from "../models/User";

export default class AdminApi extends BaseApi {
  get basePath() {
    return "/admin";
  }

  get i18nPrefix() {
    return "admin";
  }

  /**
   * Gets all users in the database
   * @returns {Promise<User[]>}>}
   */
  getUsers = async () => {
    const { data } = await this.request("GET", "users");
    return data.map((user) => new User(user));
  };

  /**
   * Sends self-service email to specific user with instrutions
   * on how to convert their account to a different role
   * @param {string} user_id
   * @param {RoleDescription} role
   * @returns {Promise<{ emailSent: boolean }>}
   */
  convertAccountEmail = async (user_id, role) => {
    const { data } = await this.request(
      "POST",
      `users/${user_id}/convert_${role.toLowerCase()}`,
      {}
    );
    return data;
  };
}
