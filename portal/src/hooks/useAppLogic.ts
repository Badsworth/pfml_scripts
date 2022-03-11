/* eslint sort-keys: ["error", "asc"] */
import useApplicationImportsLogic from "./useApplicationImportsLogic";
import useAuthLogic from "./useAuthLogic";
import useBenefitYearsLogic from "./useBenefitYearsLogic";
import useBenefitsApplicationsLogic from "./useBenefitsApplicationsLogic";
import useClaimsLogic from "./useClaimsLogic";
import useDocumentsLogic from "./useDocumentsLogic";
import useEmployersLogic from "./useEmployersLogic";
import useErrorsLogic from "./useErrorsLogic";
import useFeatureFlagsLogic from "./useFeatureFlagsLogic";
import useHolidaysLogic from "./useHolidaysLogic";
import usePaymentsLogic from "./usePaymentsLogic";
import usePortalFlow from "./usePortalFlow";
import useUsersLogic from "./useUsersLogic";

const useAppLogic = () => {
  // Utility to determine application flow
  const portalFlow = usePortalFlow();

  // State representing currently visible errors and warnings
  const errorsLogic = useErrorsLogic({ portalFlow });

  const applicationImports = useApplicationImportsLogic({
    errorsLogic,
    portalFlow,
  });
  const auth = useAuthLogic({ errorsLogic, portalFlow });

  // State representing the Portal's user object.
  // Initialize to empty user but will be populated upon the first API call
  // to fetch the user (or create the user on their first login)
  const users = useUsersLogic({
    errorsLogic,
    isLoggedIn: !!auth.isLoggedIn,
    portalFlow,
  });

  const benefitYears = useBenefitYearsLogic({ errorsLogic });

  const benefitsApplications = useBenefitsApplicationsLogic({
    errorsLogic,
    portalFlow,
  });

  const claims = useClaimsLogic({
    errorsLogic,
    portalFlow,
  });

  const documents = useDocumentsLogic({
    errorsLogic,
  });

  const employers = useEmployersLogic({
    clearClaims: claims.clearClaims,
    errorsLogic,
    portalFlow,
    setUser: users.setUser,
  });

  const featureFlags = useFeatureFlagsLogic();

  const holidays = useHolidaysLogic({
    errorsLogic,
  });

  const payments = usePaymentsLogic({
    errorsLogic,
  });

  return {
    // `_errorsLogic` should not be used except for testing
    _errorsLogic: errorsLogic,
    applicationImports,
    auth,
    benefitYears,
    benefitsApplications,
    catchError: errorsLogic.catchError,
    claims,
    // TODO (CP-886): remove once all API calls are behind appLogic
    clearErrors: errorsLogic.clearErrors,
    clearRequiredFieldErrors: errorsLogic.clearRequiredFieldErrors,
    documents,
    employers,
    errors: errorsLogic.errors,
    featureFlags,
    holidays,
    payments,
    portalFlow,
    setErrors: errorsLogic.setErrors,
    users,
  };
};

export default useAppLogic;
export type AppLogic = ReturnType<typeof useAppLogic>;
