import {
  NetworkError,
  UserNotFoundError,
  UserNotReceivedError,
} from "../errors";
import { useMemo, useState } from "react";
import UsersApi from "../api/UsersApi";
import routes from "../routes";
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
    if (!isLoggedIn) {
      throw new Error("Cannot load user before logging in to Cognito");
    }
    // Caching logic: if user has already been loaded, just reuse the cached user
    if (user) return;

    try {
      const { user, success } = await usersApi.getCurrentUser();

      if (success && user) {
        setUser(user);
        appErrorsLogic.clearErrors();
      } else {
        throw new UserNotReceivedError();
      }
    } catch (error) {
      // Show user not found error unless it's a network error
      let errorToSet;

      if (error instanceof NetworkError) {
        errorToSet = error;
      } else {
        errorToSet = new UserNotFoundError();
        // We still want to log original error
        console.error(error);
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
      // TODO CP-732: Once we switch to using a custom router we can probably use portalFlow instead of directly checking the router pathname
      !router.pathname.includes(routes.user.consentToDataSharing)
    ) {
      router.push(routes.user.consentToDataSharing);
    }
  };

  return { user, updateUser, loadUser, requireUserConsentToDataAgreement };
};

export default useUsersLogic;
