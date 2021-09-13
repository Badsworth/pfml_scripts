import React from "react";
import { useRouter } from "next/router";
import { AdminUserResponse } from "../api";
import menus, { Permission, Access } from "../menus";
import routes from "../routes";

export type Props = {
  user: AdminUserResponse;
  permissions: Permission[];
  children: React.ReactNode;
  isPage?: boolean;
};

const WithPermissions = ({
  user,
  permissions,
  isPage,
  children,
}: Props): JSX.Element => {
  const router = useRouter();
  if (!user.permissions || !user.permissions.length) return <></>;

  let has_permission = user.permissions.every((p) =>
    user.permissions?.includes(p),
  );
  // If the user does not have permission
  if (!has_permission) {
    // And if its about the whole page
    if (isPage) {
      // Find a different page for this user
      const viewableMenu = Object.entries(menus).find(([_page, _menu]) =>
        _menu.permissions.some(
          (_permission) =>
            permissions.includes(_permission) &&
            _permission.includes(Access.READ),
        ),
      );
      // And go to that page instead
      if (viewableMenu) {
        const [page, _] = viewableMenu;
        if (page !== router.pathname) {
          router.push(routes[page]);
        }
      } else {
        // Otherwise, user does not have permission to READ any page
        // Show nothing in the portal, but let devs know what's happening
        console.error(
          "You do not have the correct permissions to access the Admin Portal. Contact your administrator to confirm that you belong to the correct groups in Azure AD.",
        );
      }
    }
  }

  return <>{has_permission ? children : null}</>;
};

export default WithPermissions;
