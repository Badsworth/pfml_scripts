import {
  getMfaValidationErrors,
  setMFAPreference,
  updateMFAPhoneNumber,
} from "src/services/mfa";
import routes, { isApplicationsRoute, isEmployersRoute } from "../routes";
import { useMemo, useState } from "react";
import { ErrorsLogic } from "./useErrorsLogic";
import { PortalFlow } from "./usePortalFlow";
import RolesApi from "../api/RolesApi";
import User from "../models/User";
import UsersApi from "../api/UsersApi";

/**
 * Hook that defines user state
 */
const useUsersLogic = ({
  errorsLogic,
  isLoggedIn,
  portalFlow,
}: {
  errorsLogic: ErrorsLogic;
  isLoggedIn: boolean;
  portalFlow: PortalFlow;
}) => {
  const usersApi = useMemo(() => new UsersApi(), []);
  const rolesApi = useMemo(() => new RolesApi(), []);
  const [user, setUser] = useState<User>();

  /**
   * Update user through a PATCH request to /users
   * @param user_id - ID of user being updated
   * @param patchData - User fields to update
   */
  const updateUser = async (
    user_id: User["user_id"],
    patchData: Partial<User>
  ) => {
    errorsLogic.clearErrors();

    try {
      // Extract mfa related pieces
      const { mfa_delivery_preference, mfa_phone_number } = patchData;
      // Before triggering backend validations and updating the user, do mfa service level validation
      if (mfa_phone_number) {
        getMfaValidationErrors(mfa_phone_number?.phone_number);
      }
      // Get api validation errors and update the user
      const { user } = await usersApi.updateUser(user_id, patchData);
      // Update Cognito
      if (mfa_delivery_preference)
        await setMFAPreference(mfa_delivery_preference);
      if (mfa_phone_number?.phone_number)
        await updateMFAPhoneNumber(mfa_phone_number.phone_number);
      // Change internal state
      setUser(user);
      // Return the user only if the update did not throw any errors
      return user;
    } catch (error) {
      errorsLogic.catchError(error);
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

    errorsLogic.clearErrors();
    try {
      const { user } = await usersApi.getCurrentUser();
      setUser(user);
    } catch (error) {
      errorsLogic.catchError(error);
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

    if (!user) {
      portalFlow.goTo(routes.index, {}, { redirect: true });
      return;
    }

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
  const convertUserToEmployer = async (
    user_id: User["user_id"],
    postData: { employer_fein: string }
  ) => {
    errorsLogic.clearErrors();

    try {
      const { user } = await usersApi.convertUserToEmployer(user_id, postData);
      portalFlow.goTo(
        routes.employers.organizations,
        {
          account_converted: "true",
        },
        { redirect: true }
      );
      setUser(user);
    } catch (error) {
      errorsLogic.catchError(error);
    }
  };

  /**
   * Delete the user's employer role and leave admin associations through a DELETE to /roles
   * @param user_id - ID of user being converted
   * @param postData - User fields to update - role and leave admin
   */
  const convertUserToEmployee = async (user_id: User["user_id"]) => {
    errorsLogic.clearErrors();

    try {
      await rolesApi.deleteEmployerRole(user_id);
      const { user } = await usersApi.getCurrentUser();
      portalFlow.goTo(
        routes.applications.getReady,
        {
          account_converted: "true",
        },
        { redirect: true }
      );
      setUser(user);
    } catch (error) {
      errorsLogic.catchError(error);
    }
  };

  return {
    convertUserToEmployer,
    convertUserToEmployee,
    user,
    updateUser,
    loadUser,
    requireUserConsentToDataAgreement,
    requireUserRole,
    setUser,
  };
};

export default useUsersLogic;
export type UsersLogic = ReturnType<typeof useUsersLogic>;
