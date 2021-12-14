export enum Access {
  READ = "READ",
  CREATE = "CREATE",
  EDIT = "EDIT",
  DELETE = "DELETE",
}

export type StaticPropsPermissions = {
  props: {
    permissions: string[];
  };
};

export type Menu = {
  title: string;
  permissions: string[];
  isMainMenu?: boolean;
  isSettings?: boolean;
};

type Menus = {
  [key: string]: Menu;
};

const menus: Menus = {
  dashboard: {
    title: "Dashboard",
    permissions: ["DASHBOARD_READ"],
    isMainMenu: true,
  },
  users: {
    title: "User Lookup",
    permissions: ["USER_READ"],
    isMainMenu: true,
  },
  maintenance: {
    title: "Maintenance",
    permissions: ["MAINTENANCE_READ"],
    isMainMenu: true,
  },
  features: {
    title: "Features",
    permissions: ["FEATURES_READ"],
    isMainMenu: true,
  },
  settings: {
    title: "Settings",
    permissions: ["SETTINGS_READ"],
    isSettings: true,
  },
  help: {
    title: "Help",
    permissions: [],
    isSettings: true,
  },
};

export default menus;
