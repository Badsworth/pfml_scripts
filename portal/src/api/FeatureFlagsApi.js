import BaseApi from "./BaseApi";
import Flag from "../models/Flag";

export default class FeatureFlagApi extends BaseApi {
  get basePath() {
    return "";
  }

  get i18nPrefix() {
    return "flags";
  }

  /**
   * Fetches all feature flags
   * @returns {Promise<FeatureFlagApiResult>}
   */
  getFlags = async () => {
    const { data } = await this.request(
      "GET",
      "flags",
      null,
      {},
      { excludeAuthHeader: true }
    );

    return data.map((flag) => {
      return new Flag(flag);
    });
  };
}
