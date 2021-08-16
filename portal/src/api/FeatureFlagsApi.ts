import BaseApi from "./BaseApi";
import Flag from "../models/Flag";

export default class FeatureFlagApi extends BaseApi {
  // @ts-expect-error ts-migrate(2416) FIXME: Property 'basePath' in type 'FeatureFlagApi' is no... Remove this comment to see the full error message
  get basePath() {
    return "";
  }

  // @ts-expect-error ts-migrate(2416) FIXME: Property 'i18nPrefix' in type 'FeatureFlagApi' is ... Remove this comment to see the full error message
  get i18nPrefix() {
    return "flags";
  }

  /**
   * Fetches all feature flags
   * @returns {Promise<Array.<Object>>}
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
