import BaseApi from "./BaseApi";
/* eslint-disable jsdoc/require-returns */
import Occupation from "../models/Occupation";
import routes from "../routes";

/**
 * @typedef {{ occupations: [Occupation] }} OccupationsApiResult
 * @property {[Occupation]} [occupations] - A successful request will contain a list of occupations
 */
export default class OccupationsApi extends BaseApi {
  get basePath() {
    return routes.api.occupations;
  }

  get i18nPrefix() {
    return "occupations";
  }

  /**
   * Get the full list of occupation categories
   * @returns {Promise<OccupationsApiResult>}
   */
  getAll = async () => {
    let { data } = await this.request("GET");
    data = data.map((d) => new Occupation(d));
    return Promise.resolve(data);
  };
}
