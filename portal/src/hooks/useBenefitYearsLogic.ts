import BenefitYear from "src/models/BenefitYear";
import BenefitYearsApi from "src/api/BenefitYearsApi";
import { ErrorsLogic } from "./useErrorsLogic";
import { isFeatureEnabled } from "src/services/featureFlags";
import { useState } from "react";

const useBenefitYearsLogic = ({
  errorsLogic,
}: {
  errorsLogic: ErrorsLogic;
}) => {
  const benefitYearApi = new BenefitYearsApi();

  const [isLoadingBenefitYears, setIsLoadingBenefitYears] = useState<boolean>();
  const [benefitYearsData, setBenefitYearsData] = useState<BenefitYear[]>();

  const hasLoadedBenefitYears = () => {
    return !!benefitYearsData;
  };

  const loadBenefitYears = async () => {
    if (isLoadingBenefitYears) return;
    const shouldBenefitYearsLoad =
      isFeatureEnabled("splitClaimsAcrossBY") && !benefitYearsData;
    if (shouldBenefitYearsLoad) {
      setIsLoadingBenefitYears(true);
      errorsLogic.clearErrors();
      try {
        const benefitYears = await benefitYearApi.getBenefitYears();
        setBenefitYearsData(benefitYears);
      } catch (error) {
        errorsLogic.catchError(error);
        setBenefitYearsData([]);
      } finally {
        setIsLoadingBenefitYears(false);
      }
    }
  };

  const getCurrentBenefitYear = () => {
    if (!hasLoadedBenefitYears()) return null;
    const userHasSingleClaimant =
      new Set(benefitYearsData?.map((by) => by.employee_id)).size === 1;
    if (!userHasSingleClaimant) return null;
    return benefitYearsData?.find((by) => by.current_benefit_year);
  };

  return {
    loadBenefitYears,
    hasLoadedBenefitYears,
    getCurrentBenefitYear,
  };
};

export default useBenefitYearsLogic;
export type BenefitYearsLogic = ReturnType<typeof useBenefitYearsLogic>;
