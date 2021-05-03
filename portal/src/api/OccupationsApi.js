/* eslint-disable jsdoc/require-returns */
import Occupation, { OccupationTitle } from "../models/Occupation";

import BaseApi from "./BaseApi";
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
    data = data.map((d) => new Occupation(...d));
    return Promise.resolve({
      occupations: data,
    });
  };

  /**
   * Get the full list of occupation titles of an occupation category id
   * @returns {Promise<OccupationTitlesApiResult>}
   */
  getOccupationTitles = async (occupation_id) => {
    let { data } = await this.request("GET", occupation_id, "titles");
    data = data.map((d) => new OccupationTitle(...d));
    return Promise.resolve({
      occupation_titles: data,
    });
  };
}
