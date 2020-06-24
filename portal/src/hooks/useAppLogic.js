/* eslint sort-keys: ["error", "asc"] */
import useAuthLogic from "./useAuthLogic";
import useClaimsLogic from "./useClaimsLogic";

const useAppLogic = ({ user, setAppErrors }) => {
  // State representing the current page's url.
  // This should be updated on route changes
  // TODO write method for nextPage based on current page
  // see https://lwd.atlassian.net/wiki/spaces/CP/pages/304119860/Application+flow+logic
  // const [page, updatePage] = useState(configs.page);

  // State representing currently visible errors
  // TODO: Add appErrors hook
  // const [appErrors, setAppErrors] = useState([]);

  // user will be eventually set through a `login` method
  // const [user, setUser] = useState();
  // TODO: remove user from configs and write login method
  const {
    claims,
    loadClaims,
    createClaim,
    updateClaim,
    submitClaim,
  } = useClaimsLogic({ user });

  const auth = useAuthLogic({
    setAppErrors,
    user,
  });

  return {
    auth,
    claims,
    createClaim,
    loadClaims,
    submitClaim,
    updateClaim,
  };
};

export default useAppLogic;
