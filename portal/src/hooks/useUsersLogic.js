import {
  NetworkError,
  UserNotFoundError,
  UserNotReceivedError,
} from "../errors";
import routes, { isClaimsRoute, isEmployersRoute } from "../routes";
import { useMemo, useState } from "react";
import UsersApi from "../api/UsersApi";
import { useRouter } from "next/router";

/**
 * Hook that defines user state
 * @param {object} props
 * @param {object} props.appErrorsLogic - Utilities for set application's error  state
 * @param {Function} props.appErrorsLogic.setAppErrors - Set application error state
 * @param {object} props.portalFlow - Utilities for navigating portal application
 * @param {Function} props.portalFlow.goToNextPage - Navigate to next page in application
 * @returns {object} { user: User, loadUser: Function }
 */
const useUsersLogic = ({ appErrorsLogic, isLoggedIn, portalFlow }) => {
  const usersApi = useMemo(() => new UsersApi(), []);
  const [user, setUser] = useState();
  // TODO (CP-789): Remove dependency on next/router
  const router = useRouter();

  /**
   * Update user through a PATCH request to /users
   * @param {string} user_id - ID of user being updated
   * @param {object} patchData - User fields to update
   * @param {Claim} [claim] - Update user in the context of a claim to determine the next page route.
   */
  const updateUser = async (user_id, patchData, claim) => {
    appErrorsLogic.clearErrors();

    try {
      const { user, success } = await usersApi.updateUser(user_id, patchData);

      if (success) {
        setUser(user);

        const context = claim ? { claim, user } : { user };
        const params = claim ? { claim_id: claim.application_id } : null;
        portalFlow.goToNextPage(context, params);
      }
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Fetch the current user through a PATCH request to users/current
   * and add user to application's state
   */
  const loadUser = async () => {
    appErrorsLogic.clearErrors();

    if (!isLoggedIn) {
      throw new Error("Cannot load user before logging in to Cognito");
    }
    // Caching logic: if user has already been loaded, just reuse the cached user
    if (user) return;

    try {
      const { user } = await usersApi.getCurrentUser();

      if (!user) {
        throw new UserNotReceivedError("User not received in loadUser");
      }

      setUser(user);
    } catch (error) {
      let errorToSet;

      if (error instanceof NetworkError) {
        errorToSet = error;
      } else {
        errorToSet = new UserNotFoundError(error.message);
      }
      appErrorsLogic.catchError(errorToSet);
    }
  };

  /**
   * Redirect user to data agreement consent page if
   * they have not yet consented to the agreement.
   */
  const requireUserConsentToDataAgreement = () => {
    if (!user) throw new Error("User not loaded");
    if (
      !user.consented_to_data_sharing &&
      // TODO (CP-732): Once we switch to using a custom router we can probably use portalFlow instead of directly checking the router pathname
      !router.pathname.includes(routes.user.consentToDataSharing)
    ) {
      router.push(routes.user.consentToDataSharing);
    }
  };

  /**
   * Redirect to Employer Portal if role is employer and current page is claims route
   * redirect to Claimant Portal if role is not employer and current page is employers route
   */
  const requireUserRole = () => {
    //  Allow roles to view data sharing consent page
    const route = router.pathname;
    if (route === routes.user.consentToDataSharing) return;

    // Portal currently does not support hybrid account (both Employer AND Claimant account)
    // If user has Employer role, they cannot access Claimant Portal regardless of multiple roles
    if (!user.hasEmployerRole && isEmployersRoute(route)) {
      router.push(routes.claims.dashboard);
      return;
    }

    if (user.hasEmployerRole && isClaimsRoute(route)) {
      router.push(routes.employers.dashboard);
    }
  };

  return {
    user,
    updateUser,
    loadUser,
    requireUserConsentToDataAgreement,
    requireUserRole,
  };
};

export default useUsersLogic;
