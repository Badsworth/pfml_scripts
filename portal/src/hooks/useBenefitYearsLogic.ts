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
  const [isLoadingCrossedBenefitYears, setIsLoadingCrossedBenefitYears] =
    useState<boolean>();
  const [crossedBenefitYears, setCrossedBenefitYears] =
    useState<BenefitYear[]>();

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

  const hasLoadedCrossedBenefitYears = () => {
    return !!crossedBenefitYears;
  };

  const loadCrossedBenefitYears = async (
    employee_id: string,
    start_date: string,
    end_date: string
  ) => {
    if (isLoadingCrossedBenefitYears) return;
    const shouldCrossedBenefitYearsLoad =
      isFeatureEnabled("splitClaimsAcrossBY") && employee_id != null;
    if (shouldCrossedBenefitYearsLoad) {
      setIsLoadingCrossedBenefitYears(true);
      errorsLogic.clearErrors();
      try {
        const crossedBenefitYears = await benefitYearApi.getBenefitYears({
          employee_id,
          end_date_within: [start_date, end_date],
        });
        setCrossedBenefitYears(crossedBenefitYears);
      } catch (error) {
        errorsLogic.catchError(error);
        setCrossedBenefitYears([]);
      } finally {
        setIsLoadingCrossedBenefitYears(false);
      }
    }
  };

  const getCrossedBenefitYear = () => {
    if (!hasLoadedCrossedBenefitYears()) return null;
    if (crossedBenefitYears && crossedBenefitYears.length > 0) {
      return crossedBenefitYears[0];
    } else {
      return null;
    }
  };

  return {
    loadBenefitYears,
    hasLoadedBenefitYears,
    getCurrentBenefitYear,
    loadCrossedBenefitYears,
    hasLoadedCrossedBenefitYears,
    getCrossedBenefitYear,
  };
};

export default useBenefitYearsLogic;
export type BenefitYearsLogic = ReturnType<typeof useBenefitYearsLogic>;
