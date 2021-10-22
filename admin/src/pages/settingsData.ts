import { AzurePermission, AzureGroup } from "./settings";

/** Database table for azure groups: lk_azure_group */
export const mockLkAzureGroup = [
  {
    azure_group_id: 1,
    azure_group_name: "Admin",
  },
  {
    azure_group_id: 2,
    azure_group_name: "Dev",
  },
  {
    azure_group_id: 3,
    azure_group_name: "Contact Center",
  },
  {
    azure_group_id: 4,
    azure_group_name: "Service Desk",
  },
  {
    azure_group_id: 5,
    azure_group_name: "DFML Ops",
  },
];

/** Database table for azure permissions: lk_azure_permission */
export const mockLkAzurePermission = [
  {
    azure_permission_id: 1,
    azure_permission_name: "User Lookup",
  },
  {
    azure_permission_id: 2,
    azure_permission_name: "View Logs",
  },
  {
    azure_permission_id: 3,
    azure_permission_name: "Convert Account",
  },
  {
    azure_permission_id: 4,
    azure_permission_name: "Login as User",
  },
  {
    azure_permission_id: 5,
    azure_permission_name: "View Permissions",
  },
  {
    azure_permission_id: 6,
    azure_permission_name: "Configure Permissions",
  },
  {
    azure_permission_id: 7,
    azure_permission_name: "View Maintenance",
  },
  {
    azure_permission_id: 8,
    azure_permission_name: "Configure Maintenance",
  },
  {
    azure_permission_id: 9,
    azure_permission_name: "View Features",
  },
  {
    azure_permission_id: 10,
    azure_permission_name: "Configure Features",
  },
  {
    azure_permission_id: 11,
    azure_permission_name: "View Dashboard",
  },
];

/** Mock data from mock api endpoint: /azure/permissions */
export const getAzurePermissions: AzurePermission[] = [
  {
    azure_permission_id: 1,
    azure_permission_name: "User Lookup",
    groups: [
      {
        azure_group_id: 1,
        azure_group_name: "Admin",
      },
      {
        azure_group_id: 2,
        azure_group_name: "Dev",
      },
      {
        azure_group_id: 3,
        azure_group_name: "Contact Center",
      },
      {
        azure_group_id: 4,
        azure_group_name: "Service Desk",
      },
      {
        azure_group_id: 5,
        azure_group_name: "DFML Ops",
      },
    ],
  },
  {
    azure_permission_id: 2,
    azure_permission_name: "View Logs",
    groups: [
      {
        azure_group_id: 1,
        azure_group_name: "Admin",
      },
      {
        azure_group_id: 2,
        azure_group_name: "Dev",
      },
      {
        azure_group_id: 5,
        azure_group_name: "DFML Ops",
      },
    ],
  },
  {
    azure_permission_id: 3,
    azure_permission_name: "Convert Account",
    groups: [
      {
        azure_group_id: 1,
        azure_group_name: "Admin",
      },
      {
        azure_group_id: 2,
        azure_group_name: "Dev",
      },
      {
        azure_group_id: 3,
        azure_group_name: "Contact Center",
      },
    ],
  },
  {
    azure_permission_id: 4,
    azure_permission_name: "Login as User",
    groups: [
      {
        azure_group_id: 1,
        azure_group_name: "Admin",
      },
      {
        azure_group_id: 2,
        azure_group_name: "Dev",
      },
    ],
  },
  {
    azure_permission_id: 5,
    azure_permission_name: "View Permissions",
    groups: [
      {
        azure_group_id: 1,
        azure_group_name: "Admin",
      },
      {
        azure_group_id: 2,
        azure_group_name: "Dev",
      },
      {
        azure_group_id: 5,
        azure_group_name: "DFML Ops",
      },
    ],
  },
  {
    azure_permission_id: 6,
    azure_permission_name: "Configure Permissions",
    groups: [
      {
        azure_group_id: 1,
        azure_group_name: "Admin",
      },
    ],
  },
  {
    azure_permission_id: 7,
    azure_permission_name: "View Maintenance",
    groups: [
      {
        azure_group_id: 1,
        azure_group_name: "Admin",
      },
      {
        azure_group_id: 2,
        azure_group_name: "Dev",
      },
      {
        azure_group_id: 5,
        azure_group_name: "DFML Ops",
      },
    ],
  },
  {
    azure_permission_id: 8,
    azure_permission_name: "Configure Maintenance",
    groups: [
      {
        azure_group_id: 1,
        azure_group_name: "Admin",
      },
      {
        azure_group_id: 2,
        azure_group_name: "Dev",
      },
    ],
  },
  {
    azure_permission_id: 9,
    azure_permission_name: "View Features",
    groups: [
      {
        azure_group_id: 1,
        azure_group_name: "Admin",
      },
      {
        azure_group_id: 2,
        azure_group_name: "Dev",
      },
      {
        azure_group_id: 5,
        azure_group_name: "DFML Ops",
      },
    ],
  },
  {
    azure_permission_id: 10,
    azure_permission_name: "Configure Features",
    groups: [
      {
        azure_group_id: 1,
        azure_group_name: "Admin",
      },
      {
        azure_group_id: 2,
        azure_group_name: "Dev",
      },
    ],
  },
  {
    azure_permission_id: 11,
    azure_permission_name: "View Dashboard",
    groups: [
      {
        azure_group_id: 1,
        azure_group_name: "Admin",
      },
      {
        azure_group_id: 2,
        azure_group_name: "Dev",
      },
      {
        azure_group_id: 5,
        azure_group_name: "DFML Ops",
      },
    ],
  },
];

/** Mock data from mock api endpoint: /azure/groups */
export const getAzureGroups: AzureGroup[] = [
  {
    azure_group_id: 1,
    azure_group_name: "Admin",
  },
  {
    azure_group_id: 3,
    azure_group_name: "Contact Center",
  },
  {
    azure_group_id: 5,
    azure_group_name: "DFML Ops",
  },
  {
    azure_group_id: 2,
    azure_group_name: "Dev",
  },
  {
    azure_group_id: 4,
    azure_group_name: "Service Desk",
  },
];
