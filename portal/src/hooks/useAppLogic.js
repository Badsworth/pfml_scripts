/* eslint sort-keys: ["error", "asc"] */
import useAppErrorsLogic from "./useAppErrorsLogic";
import useAuthLogic from "./useAuthLogic";
import useClaimsLogic from "./useClaimsLogic";
import useDocumentsLogic from "./useDocumentsLogic";
import usePortalFlow from "./usePortalFlow";
import useUsersLogic from "./useUsersLogic";

const useAppLogic = () => {
  // Utility to determine application flow
  const portalFlow = usePortalFlow();

  // State representing currently visible errors and warnings
  const { appErrors, ...appErrorsLogic } = useAppErrorsLogic();
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
  const claims = useClaimsLogic({
    appErrorsLogic,
    portalFlow,
    user: users.user,
  });

  const documents = useDocumentsLogic({
    appErrorsLogic,
    portalFlow,
  });

  return {
    appErrors,
    auth,
    claims,
    // TODO (CP-886): remove once all API calls are behind appLogic
    clearErrors: appErrorsLogic.clearErrors,
    documents,
    goToNextPage: portalFlow.goToNextPage,
    setAppErrors: appErrorsLogic.setAppErrors,
    users,
  };
};

export default useAppLogic;
