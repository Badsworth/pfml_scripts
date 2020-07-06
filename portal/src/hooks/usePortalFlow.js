import { Machine } from "xstate";
import { RouteTransitionError } from "../errors";
import machineConfigs from "../routes/claim-flow-configs";
import { useMemo } from "react";
import { useRouter } from "next/router";

/**
 * Hook that provides methods for convenient page routing
 * @param {object} props - object of props
 * @param {User} props.user - instance of current User
 * @returns {object} { goToNextPage: Function, currentPageRoute: string } -
 */
const usePortalFlow = ({ user }) => {
  const routingMachine = useMemo(() => Machine(machineConfigs), []);
  // TODO use custom useRouter: see https://github.com/EOLWD/pfml/pull/561/files#r448590332
  const router = useRouter();
  // State representing current page route
  const { pathname: page } = router;

  /**
   * Navigate to the next page in the flow given a user and claim context
   * @param {object} context - additional context used to determine next page
   */
  const goToNextPage = (context) => {
    const ctx = Object.assign({ user }, context);
    const nextRoutingMachine = routingMachine.withContext(ctx);

    const nextPageRoute = nextRoutingMachine.transition(page, "CONTINUE");

    if (!nextPageRoute) {
      throw new RouteTransitionError();
    }

    router.push(nextPageRoute.value);
  };

  return { page, goToNextPage };
};

export default usePortalFlow;
