import React from "react";
import { useRouter } from "next/router";
import { AdminUserResponse } from "../api";
import menus, { Access } from "../menus";
import routes from "../routes";

export type Props = {
  user: AdminUserResponse;
  permissions: string[];
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
  const user_permissions = user?.permissions || [];
  if (!user_permissions.length) return <></>;

  let has_permission = permissions.every((p) => user_permissions.includes(p));
  // If the user does not have permission
  if (!has_permission) {
    // And if its about the whole page
    if (isPage) {
      // Find a different page for this user
      const viewableMenu = Object.entries(menus).find(([_page, _menu]) =>
        _menu.permissions.some(
          (_permission) =>
            user.permissions &&
            user.permissions.length &&
            user.permissions.includes(_permission) &&
            _permission.includes(Access.READ),
        ),
      );
      // And go to that page instead
      // Otherwise, user does not have permission to READ any page
      // Show nothing in the portal, but let devs know what's happening
      if (viewableMenu) {
        const [page, _] = viewableMenu;
        if (page !== router.pathname) {
          router.push(routes[page]);
        }
      }
    }
  }

  return <>{has_permission ? children : null}</>;
};

export default WithPermissions;
