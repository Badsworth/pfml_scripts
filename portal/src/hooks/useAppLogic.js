/* eslint sort-keys: ["error", "asc"] */
import useAppErrorsLogic from "./useAppErrorsLogic";
import useAuthLogic from "./useAuthLogic";
import useClaimsLogic from "./useClaimsLogic";

const useAppLogic = ({ user }) => {
  // State representing the current page's url.
  // This should be updated on route changes
  // TODO write method for nextPage based on current page
  // see https://lwd.atlassian.net/wiki/spaces/CP/pages/304119860/Application+flow+logic
  // const [page, updatePage] = useState(configs.page);

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
  } = useClaimsLogic({ appErrorsLogic, user });

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
    loadClaims,
    // TODO: remove once all API calls are behind appLogic
    setAppErrors: appErrorsLogic.setAppErrors,
    submitClaim,
    updateClaim,
  };
};

export default useAppLogic;
