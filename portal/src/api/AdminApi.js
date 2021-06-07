import BaseApi from "./BaseApi";
import Flag from "../models/Flag";

export default class AdminApi extends BaseApi {
  get basePath() {
    return "";
  }

  get i18nPrefix() {
    return "flag";
  }

  /**
   * Fetches a feature flag
   * @param {string} flag_name - Name of flag to retrieve
   * @returns {Promise<AdminApiResult>}
   */
  getFlag = async flag_name => {
    const { data } = await this.request("GET", "flags/" + flag_name, null, {}, { excludeAuthHeader: true });

    if(Array.isArray(data)) {
      return new Flag(data);
    } else {
      return [new Flag(data)];
    }
  };
}
