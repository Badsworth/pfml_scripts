import routes, { isApplicationsRoute, isEmployersRoute } from "../routes";
import { useMemo, useState } from "react";
import BenefitsApplication from "../models/BenefitsApplication";
import User from "../models/User";
import { UserNotReceivedError } from "../errors";
import UsersApi from "../api/UsersApi";
import useAppErrorsLogic from "./useAppErrorsLogic";
import usePortalFlow from "./usePortalFlow";

/**
 * Hook that defines user state
 */
const useUsersLogic = ({
  appErrorsLogic,
  isLoggedIn,
  portalFlow,
}: {
  appErrorsLogic: ReturnType<typeof useAppErrorsLogic>;
  isLoggedIn: boolean;
  portalFlow: ReturnType<typeof usePortalFlow>;
}) => {
  const usersApi = useMemo(() => new UsersApi(), []);
  const [user, setUser] = useState<User>();

  /**
   * Update user through a PATCH request to /users
   * @param user_id - ID of user being updated
   * @param patchData - User fields to update
   * @param [claim] - Update user in the context of a claim to determine the next page route.
   */
  const updateUser = async (
    user_id: User["user_id"],
    patchData: Partial<User>,
    claim?: BenefitsApplication
  ) => {
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

    // Portal currently does not support hybrid account (both Employer AND Claimant account)
    // If user has Employer role, they cannot access Claimant Portal regardless of multiple roles
    if (!user.hasEmployerRole && isEmployersRoute(pathname)) {
      portalFlow.goTo(routes.applications.index, {}, { redirect: true });
      return;
    }

    if (user.hasEmployerRole && isApplicationsRoute(pathname)) {
      portalFlow.goTo(routes.employers.welcome, {}, { redirect: true });
    }
  };

  /**
   * Convert user role through a POST request to /users/{user_id}/convert_employer
   * @param user_id - ID of user being converted
   * @param postData - User fields to update - role and leave admin
   */
  const convertUser = async (
    user_id: User["user_id"],
    postData: { employer_fein: string }
  ) => {
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

  return {
    convertUser,
    user,
    updateUser,
    loadUser,
    requireUserConsentToDataAgreement,
    requireUserRole,
    setUser,
  };
};

export default useUsersLogic;
