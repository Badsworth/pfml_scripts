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
  heroIconName?: string;
};

type Menus = {
  [key: string]: Menu;
};

const menus: Menus = {
  dashboard: {
    title: "Dashboard",
    permissions: ["DASHBOARD_READ"],
    isMainMenu: true,
    heroIconName: "HomeIcon",
  },
  users: {
    title: "User Lookup",
    permissions: ["USER_READ"],
    isMainMenu: true,
    heroIconName: "UsersIcon",
  },
  maintenance: {
    title: "Maintenance",
    permissions: ["MAINTENANCE_READ"],
    isMainMenu: true,
    heroIconName: "ExclamationCircleIcon",
  },
  features: {
    title: "Features",
    permissions: ["FEATURES_READ"],
    isMainMenu: true,
    heroIconName: "FlagIcon",
  },
  settings: {
    title: "Settings",
    permissions: ["SETTINGS_READ"],
    isSettings: true,
    heroIconName: "CogIcon",
  },
  help: {
    title: "Help",
    permissions: [],
    isSettings: true,
    heroIconName: "QuestionMarkCircleIcon",
  },
};

export default menus;
