import BaseApi from "./BaseApi";
import BenefitYear from "src/models/BenefitYear";
import routes from "src/routes";

export interface GetBenefitYearParams {
  employee_id?: string;
  current?: boolean;
  end_date_within?: [string, string];
}
export default class BenefitYearsApi extends BaseApi {
  get namespace(): string {
    return "benefitYears";
  }

  get basePath(): string {
    return routes.api.benefitYears;
  }

  get i18nPrefix(): string {
    return "benefitYears";
  }

  getBenefitYears = async (params: GetBenefitYearParams = {}) => {
    const { data } = await this.request<BenefitYear[]>("POST", "search", {
      terms: { ...params },
    });

    return data;
  };
}
