import BaseApi from "./BaseApi";
import Flag from "../models/Flag";

export default class FeatureFlagApi extends BaseApi {
  get basePath() {
    return "";
  }

  get namespace() {
    return "flags";
  }

  /**
   * Fetches all feature flags
   * @returns {Promise<Array.<Object>>}
   */
  getFlags = async () => {
    const { data } = await this.request<Flag[]>("GET", "flags", undefined, {
      excludeAuthHeader: true,
    });

    return data.map((flag) => {
      return new Flag(flag);
    });
  };
}
