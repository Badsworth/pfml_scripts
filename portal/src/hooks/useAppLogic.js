/* eslint sort-keys: ["error", "asc"] */
import useAppErrorsLogic from "./useAppErrorsLogic";
import useAuthLogic from "./useAuthLogic";
import useClaimsLogic from "./useClaimsLogic";
import usePortalFlow from "./usePortalFlow";

const useAppLogic = ({ user }) => {
  // utility to determine application flow
  const portalFlow = usePortalFlow({ user });

  // State representing currently visible errors and warnings
  const { appErrors, ...appErrorsLogic } = useAppErrorsLogic();

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
    // TODO: remove once all API calls are behind appLogic
    setAppErrors: appErrorsLogic.setAppErrors,
    submitClaim,
    updateClaim,
  };
};

export default useAppLogic;
