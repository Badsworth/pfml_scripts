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
  const { user, setUser, updateUser, loadUser } = useUsersLogic({
    appErrorsLogic,
    portalFlow,
  });

  // user will be eventually set through a `login` method
  // const [user, setUser] = useState();
  // TODO: remove user from configs and write login method
  const {
    claims,
    loadClaims,
    createClaim,
    updateClaim,
    submitClaim,
  } = useClaimsLogic({ appErrorsLogic, portalFlow, user });

  const auth = useAuthLogic({
    appErrorsLogic,
    user,
  });

  return {
    appErrors,
    auth,
    claims,
    // TODO: remove once all API calls are behind appLogic
    clearErrors: appErrorsLogic.clearErrors,
    createClaim,
    // TODO: remove once user api calls are behind appLogic
    goToNextPage: portalFlow.goToNextPage,
    loadClaims,
    loadUser,
    // TODO: remove once all API calls are behind appLogic
    setAppErrors: appErrorsLogic.setAppErrors,
    setUser,
    submitClaim,
    updateClaim,
    updateUser,
    user,
  };
};

export default useAppLogic;
