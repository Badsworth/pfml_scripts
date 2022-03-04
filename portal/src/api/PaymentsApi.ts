import BaseApi from "./BaseApi";
import { Payment } from "../models/Payment";
import routes from "../routes";

export default class PaymentsApi extends BaseApi {
  get basePath() {
    return routes.api.payments;
  }

  get namespace() {
    return "payments";
  }

  /**
   * Fetches payments given a FINEOS absence ID
   */
  getPayments = async (absenceId: string) => {
    const { data } = await this.request<Payment>("GET", "", {
      absence_case_id: absenceId,
    });

    return {
      payments: new Payment(data),
    };
  };
}
