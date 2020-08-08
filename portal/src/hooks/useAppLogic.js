/* eslint sort-keys: ["error", "asc"] */
import useAppErrorsLogic from "./useAppErrorsLogic";
import useAuthLogic from "./useAuthLogic";
import useClaimsLogic from "./useClaimsLogic";
import usePortalFlow from "./usePortalFlow";
import useUsersLogic from "./useUsersLogic";

const useAppLogic = () => {
  // Utility to determine application flow
  const portalFlow = usePortalFlow();

  // State representing currently visible errors and warnings
  const { appErrors, ...appErrorsLogic } = useAppErrorsLogic();

  // State representing the Portal's user object.
  // Initialize to empty user but will be populated upon the first API call
  // to fetch the user (or create the user on their first login)
  const users = useUsersLogic({ appErrorsLogic, portalFlow });

  // user will be eventually set through a `login` method
  // const [user, setUser] = useState();
  // TODO: remove user from configs and write login method
  const claims = useClaimsLogic({
    appErrorsLogic,
    portalFlow,
    user: users.user,
  });

  const auth = useAuthLogic({ appErrorsLogic });

  return {
    appErrors,
    auth,
    claims,
    // TODO: remove once all API calls are behind appLogic
    clearErrors: appErrorsLogic.clearErrors,
    goToNextPage: portalFlow.goToNextPage,
    setAppErrors: appErrorsLogic.setAppErrors,
    users,
  };
};

export default useAppLogic;
