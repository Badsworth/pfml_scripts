import {
  NetworkError,
  UserNotFoundError,
  UserNotReceivedError,
} from "../errors";
import { useMemo, useState } from "react";
import UsersApi from "../api/UsersApi";

/**
 * Hook that defines user state
 * @param {object} props
 * @param {object} props.appErrorsLogic - Utilities for set application's error  state
 * @param {Function} props.appErrorsLogic.setAppErrors - Set application error state
 * @param {object} props.portalFlow - Utilities for navigating portal application
 * @param {Function} props.portalFlow.goToNextPage - Navigate to next page in application
 * @returns {object} { user: User, loadUser: Function }
 */
const useUsersLogic = ({ appErrorsLogic, portalFlow }) => {
  const usersApi = useMemo(() => new UsersApi(), []);
  const [user, setUser] = useState();

  /**
   * Update user through a PATCH request to /users
   * @param {string} user_id - ID of user being updated
   * @param {object} patchData - User fields to update
   * @param {Claim} [claim] - Update user in the context of a claim to determine the next page route.
   */
  const updateUser = async (user_id, patchData, claim) => {
    try {
      const { user } = await usersApi.updateUser(user_id, patchData);

      setUser(user);

      const context = claim ? { claim, user } : { user };
      const params = claim ? { claim_id: claim.application_id } : null;
      portalFlow.goToNextPage(context, params);

      appErrorsLogic.clearErrors();
    } catch (error) {
      appErrorsLogic.catchError(error);
    }
  };

  /**
   * Fetch the current user through a PATCH request to users/current
   * and add user to applicaiton's state
   */
  const loadUser = async () => {
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

  return { user, setUser, updateUser, loadUser };
};

export default useUsersLogic;
