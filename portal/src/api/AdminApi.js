import BaseApi from "./BaseApi";

export default class AdminApi extends BaseApi {
  get basePath() {
    return "";
  }

  get i18nPrefix() {
    return "flag";
  }

  /**
   * Fetches a feature flag
   */
   getFlag = async (flag_name) => {
    const { data } = await this.request("GET", "flags/" + flag_name, null, {}, { excludeAuthHeader: true });

    if(Array.isArray(data)) {
      return data;
    } else {
      return [data];
    }
  };
}
