import BaseApi from "./BaseApi";
import BenefitYear from "src/models/BenefitYear";
import routes from "src/routes";

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

  getBenefitYears = async () => {
    const { data } = await this.request<BenefitYear[]>("POST", "search", {});

    return data;
  };
}
