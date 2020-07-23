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
  const {
    claims,
    loadClaims,
    createClaim,
    updateClaim,
    submitClaim,
  } = useClaimsLogic({ appErrorsLogic, portalFlow, user: users.user });

  const auth = useAuthLogic({ appErrorsLogic });

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
    // TODO: remove once all API calls are behind appLogic
    setAppErrors: appErrorsLogic.setAppErrors,
    submitClaim,
    updateClaim,
    updateUser: users.updateUser, // TODO (CP-725): Remove this once all references to `appLogic.updateUser` use the nested object `appLogic.users.updateUser`,
    user: users.user, // TODO (CP-725): Remove this once all references to `appLogic.user` use the nested object `appLogic.users.user`,
    users,
  };
};

export default useAppLogic;
