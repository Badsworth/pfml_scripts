/* eslint sort-keys: ["error", "asc"] */
import useAppErrorsLogic from "./useAppErrorsLogic";
import useAuthLogic from "./useAuthLogic";
import useBenefitsApplicationsLogic from "./useBenefitsApplicationsLogic";
import useClaimsLogic from "./useClaimsLogic";
import useDocumentsLogic from "./useDocumentsLogic";
import useEmployersLogic from "./useEmployersLogic";
import useFlagsLogic from "./useFeatureFlagsLogic";
import useOtherLeavesLogic from "./useOtherLeavesLogic";
import usePortalFlow from "./usePortalFlow";
import useUsersLogic from "./useUsersLogic";

const useAppLogic = () => {
  // Utility to determine application flow
  const portalFlow = usePortalFlow();

  // State representing currently visible errors and warnings
  const { appErrors, ...appErrorsLogic } = useAppErrorsLogic({ portalFlow });
  const auth = useAuthLogic({ appErrorsLogic, portalFlow });

  // State representing the Portal's user object.
  // Initialize to empty user but will be populated upon the first API call
  // to fetch the user (or create the user on their first login)
  const users = useUsersLogic({
    appErrorsLogic,
    isLoggedIn: auth.isLoggedIn,
    portalFlow,
  });

  // user will be eventually set through a `login` method
  // const [user, setUser] = useState();
  // TODO (CP-885): remove user from configs and write login method
  const benefitsApplications = useBenefitsApplicationsLogic({
    appErrorsLogic,
    portalFlow,
    user: users.user,
  });

  const claims = useClaimsLogic({
    appErrorsLogic,
  });

  const documents = useDocumentsLogic({
    appErrorsLogic,
    portalFlow,
  });

  const employers = useEmployersLogic({
    appErrorsLogic,
    portalFlow,
    setUser: users.setUser,
  });

  const otherLeaves = useOtherLeavesLogic({ appErrorsLogic });
  const featureFlags = useFlagsLogic({ appErrorsLogic });

  return {
    appErrors,
    auth,
    benefitsApplications,
    catchError: appErrorsLogic.catchError,
    claims,
    // TODO (CP-886): remove once all API calls are behind appLogic
    clearErrors: appErrorsLogic.clearErrors,
    documents,
    employers,
    otherLeaves,
    portalFlow,
    setAppErrors: appErrorsLogic.setAppErrors,
    users,
    featureFlags,
  };
};

export default useAppLogic;
