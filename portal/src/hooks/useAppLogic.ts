/* eslint sort-keys: ["error", "asc"] */
import useAppErrorsLogic from "./useAppErrorsLogic";
import useAuthLogic from "./useAuthLogic";
import useBenefitsApplicationsLogic from "./useBenefitsApplicationsLogic";
import useClaimsLogic from "./useClaimsLogic";
import useDocumentsLogic from "./useDocumentsLogic";
import useEmployersLogic from "./useEmployersLogic";
import useFeatureFlagsLogic from "./useFeatureFlagsLogic";
import usePortalFlow from "./usePortalFlow";
import useUsersLogic from "./useUsersLogic";

const useAppLogic = () => {
  // Utility to determine application flow
  const portalFlow = usePortalFlow();

  // State representing currently visible errors and warnings
  const appErrorsLogic = useAppErrorsLogic({ portalFlow });
  const auth = useAuthLogic({ appErrorsLogic, portalFlow });

  // State representing the Portal's user object.
  // Initialize to empty user but will be populated upon the first API call
  // to fetch the user (or create the user on their first login)
  const users = useUsersLogic({
    appErrorsLogic,
    isLoggedIn: !!auth.isLoggedIn,
    portalFlow,
  });

  const benefitsApplications = useBenefitsApplicationsLogic({
    appErrorsLogic,
    portalFlow,
  });

  const claims = useClaimsLogic({
    appErrorsLogic,
    portalFlow,
  });

  const documents = useDocumentsLogic({
    appErrorsLogic,
  });

  const employers = useEmployersLogic({
    appErrorsLogic,
    clearClaims: claims.clearClaims,
    portalFlow,
    setUser: users.setUser,
  });

  const featureFlags = useFeatureFlagsLogic();

  return {
    // `_appErrorsLogic` should not be used except for testing
    _appErrorsLogic: appErrorsLogic,
    appErrors: appErrorsLogic.appErrors,
    auth,
    benefitsApplications,
    catchError: appErrorsLogic.catchError,
    claims,
    // TODO (CP-886): remove once all API calls are behind appLogic
    clearErrors: appErrorsLogic.clearErrors,
    clearRequiredFieldErrors: appErrorsLogic.clearRequiredFieldErrors,
    documents,
    employers,
    featureFlags,
    portalFlow,
    setAppErrors: appErrorsLogic.setAppErrors,
    users,
  };
};

export default useAppLogic;
export type AppLogic = ReturnType<typeof useAppLogic>;