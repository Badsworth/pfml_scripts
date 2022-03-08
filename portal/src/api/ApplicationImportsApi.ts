import BaseApi from "./BaseApi";
import BenefitsApplication from "../models/BenefitsApplication";
import routes from "../routes";

export default class ApplicationImportsApi extends BaseApi {
  get basePath() {
    return routes.api.applicationImports;
  }

  get namespace() {
    return "applicationImports";
  }

  importClaim = async (postData: {
    absence_case_id: string | null;
    tax_identifier: string | null;
  }) => {
    const { data } = await this.request<BenefitsApplication>(
      "POST",
      "",
      postData
    );

    return new BenefitsApplication(data);
  };
}
