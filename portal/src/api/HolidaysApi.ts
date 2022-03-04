import BaseApi from "./BaseApi";
import { Holiday } from "../models/Holiday";
import routes from "../routes";

export default class HolidaysApi extends BaseApi {
  get basePath() {
    return routes.api.holidays;
  }

  get i18nPrefix() {
    return "holidays";
  }

  /**
   * Fetches holidays in a date range
   */
  getHolidays = async (start_date: string, end_date: string) => {
    const { data } = await this.request<Holiday>("POST", "search", {
      start_date,
      end_date,
    });
    return data;
  };
}
