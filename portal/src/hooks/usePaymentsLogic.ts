import { AppErrorsLogic } from "./useAppErrorsLogic";
import { Payment } from "../models/Payment";
import PaymentsApi from "../api/PaymentsApi";
import { isFeatureEnabled } from "../services/featureFlags";
import { useState } from "react";

const usePaymentsLogic = ({
  appErrorsLogic,
}: {
  appErrorsLogic: AppErrorsLogic;
}) => {
  const paymentsApi = new PaymentsApi();

  /**
   * Check if payments are loading for a claim
   */
  const [isLoadingPayments, setIsLoadingPayments] = useState<boolean>();

  /**
   * Payments data associated with claim
   */
  const [loadedPaymentsData, setLoadedPaymentsData] = useState<Payment>();

  /**
   * Check if payments have loaded for claim
   */
  const hasLoadedPayments = (absenceId: string) =>
    loadedPaymentsData?.absence_case_id === absenceId;

  /**
   * Load payments for a single claim. Note that if there is already a payment being loaded then
   * this function will immediately return undefined.
   */
  const loadPayments = async (absenceId: string) => {
    if (isLoadingPayments) return;

    const shouldPaymentsLoad =
      isFeatureEnabled("claimantShowPaymentsPhaseTwo") &&
      !hasLoadedPayments(absenceId);
    if (shouldPaymentsLoad) {
      setIsLoadingPayments(true);
      appErrorsLogic.clearErrors();
      try {
        const { payments } = await paymentsApi.getPayments(absenceId);
        setLoadedPaymentsData(new Payment(payments));
      } catch (error) {
        appErrorsLogic.catchError(error);
      } finally {
        setIsLoadingPayments(false);
      }
    }
  };

  return {
    loadPayments,
    loadedPaymentsData,
    hasLoadedPayments,
    isLoadingPayments,
  };
};
export default usePaymentsLogic;
export type PaymentsLogic = ReturnType<typeof usePaymentsLogic>;