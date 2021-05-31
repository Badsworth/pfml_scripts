import {
  UnauthorizedError,
  UserNotFoundError,
  UserNotReceivedError,
} from "../errors";
import routes, {
  isAdminRoute,
  isApplicationsRoute,
  isEmployersRoute,
} from "../routes";
import { useMemo, useState } from "react";

import AdminApi from "../api/AdminApi";
import UsersApi from "../api/UsersApi";
import tracker from "../services/tracker";

/**
 * Hook that defines user state
 * @param {object} props
 * @param {object} props.appErrorsLogic - Utilities for set application's error  state
 * @param {boolean} props.isLoggedIn
 * @param {object} props.portalFlow - Utilities for navigating portal application
 * @returns {object} { user: User, loadUser: Function }
 */
const useUsersLogic = ({ appErrorsLogic, isLoggedIn, portalFlow }) => {
  const usersApi = useMemo(() => new UsersApi(), []);
  const adminApi = useMemo(() => new AdminApi(), []);
  const [user, setUser] = useState();

  /**
   * Update user through a PATCH request to /users
   * @param {string} user_id - ID of user being updated
   * @param {object} patchData - User fields to update
   * @param {BenefitsApplication} [claim] - Update user in the context of a claim to determine the next page route.
   */
  const updateUser = async (user_id, patchData, claim) => {
    appErrorsLogic.clearErrors();

    try {
      const { user } = await usersApi.updateUser(user_id, patchData);

      setUser(user);

      const context = claim ? { claim, user } : { user };
      const params = claim ? { claim_id: claim.application_id } : null;
      portalFlow.goToNextPage(context, params);
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Fetch the current user through a PATCH request to users/current
   * and add user to application's state
   */
  const loadUser = async () => {
    if (!isLoggedIn) {
      throw new Error("Cannot load user before logging in to Cognito");
    }
    // Caching logic: if user has already been loaded, just reuse the cached user
    if (user) return;

    appErrorsLogic.clearErrors();
    try {
      const { user } = await usersApi.getCurrentUser();

      if (!user) {
        throw new UserNotReceivedError("User not received in loadUser");
      }

      setUser(user);
    } catch (error) {
      if (error instanceof UnauthorizedError) {
        // TODO (CP-1768): Remove this block once sign up requests are always sent through API.
        // API returns a 401 (UnauthorizedError) if they don't find a matching
        // user in the database. This could mean our post-confirmation hook
        // timed out or failed. We redirect the user to the password reset
        // page, which triggers the post confirmation hook again upon a reset.
        tracker.noticeError(new UserNotFoundError(error.message));
        portalFlow.goTo(routes.auth.resetPassword, { "user-not-found": true });

        return;
      }

      appErrorsLogic.catchError(error);
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
      !portalFlow.pathname.includes(routes.user.consentToDataSharing)
    ) {
      portalFlow.goTo(routes.user.consentToDataSharing);
    }
  };

  /**
   * Redirect to Employer Portal if role is employer and current page is claims route
   * redirect to Claimant Portal if role is not employer and current page is employers route
   */
  const requireUserRole = () => {
    //  Allow roles to view data sharing consent page
    const pathname = portalFlow.pathname;
    if (pathname === routes.user.consentToDataSharing) return;

    const isNotAdmin = !user.hasAdminRole && isAdminRoute(pathname);
    const isNotEmployer = !user.hasEmployerRole && isEmployersRoute(pathname);
    // Portal currently does not support hybrid account (both Employer AND Claimant account)
    // If user has Employer role, they cannot access Claimant Portal regardless of multiple roles
    if (isNotEmployer || isNotAdmin) {
      portalFlow.goTo(routes.applications.index);
      return;
    }

    if (user.hasEmployerRole && isApplicationsRoute(pathname)) {
      portalFlow.goTo(routes.employers.welcome);
    }
  };

  const getUsers = () => {
    if (user.hasAdminRole) {
      return adminApi.getUsers();
    }
    return [];
  };

  const convertUserToEmployer = (user_id) => {
    if (user.hasAdminRole) {
      return adminApi.convertUserToEmployer(user_id);
    }
    return false;
  };
  /**
   * Convert user role through a POST request to /users/{user_id}/convert_employer
   * @param {string} user_id - ID of user being converted
   * @param {object} postData - User fields to update - role and leave admin
   */
  const convertUser = async (user_id, postData) => {
    appErrorsLogic.clearErrors();

    try {
      const { user } = await usersApi.convertUser(user_id, postData);

      setUser(user);

      portalFlow.goTo(routes.employers.organizations, {
        account_converted: true,
      });
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  const getUsers = () => {
    if (user.hasAdminRole) {
      return adminApi.getUsers();
    }
    return [];
  };

  const convertUserToEmployer = (user_id) => {
    if (user.hasAdminRole) {
      return adminApi.convertUserToEmployer(user_id);
    }
    return false;
  };

  const getUsers = () => {
    if (user.hasAdminRole) {
      return adminApi.getUsers();
    }
    return [];
  };

  const convertUserToEmployer = (user_id) => {
    if (user.hasAdminRole) {
      return adminApi.convertUserToEmployer(user_id);
    }
    return false;
  };

  return {
    convertUser,
    user,
    updateUser,
    loadUser,
    requireUserConsentToDataAgreement,
    requireUserRole,
    setUser,
    admin: {
      getUsers,
      convertUserToEmployer,
    },
  };
};

export default useUsersLogic;
