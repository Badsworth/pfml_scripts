import Alert from "../components/Alert";
import Button from "../components/Button";
import { Helmet } from "react-helmet-async";
import { isEqual } from "lodash";
import React, { useEffect, useState } from "react";
//import { ApiResponse, PermissionsResponse, AzureGroupsResponse, getPermissions, patchPermissions, getAzureGroups } from "../api";
// @todo: Remove when API is functional
import { getAzureGroups, getAzurePermissions } from "./settingsData";

export type AzureGroup = {
  azure_group_id: number;
  azure_group_name: string;
};

export type AzurePermission = {
  azure_permission_id: number;
  azure_permission_name: string;
  groups: AzureGroup[];
};

export default function Settings() {
  type PermissionState = {
    // What you see in the UI.
    current: AzurePermission[];
    // The originally loaded state when the page is loaded. Also reset after a
    // successful save.
    original: AzurePermission[];
    // Holds an array of ONLY the changed permissions so the payload to the
    // server is minimal.
    updated: AzurePermission[];
  };

  const initialAzurePermissionsState = {
    current: [],
    original: [],
    updated: [],
  };

  // State for permissions: current, original and updated
  const [azurePermissions, setAzurePermissions] = useState<PermissionState>(
    initialAzurePermissionsState,
  );
  // Azure groups stored in our DB from our API. Used for reference
  // when building the table
  const [azureGroups, setAzureGroups] = useState<AzureGroup[]>([]);
  // State for success alert
  const [saved, setSaved] = useState<boolean>(false);
  // State for error alert
  const [error, setError] = useState<boolean>(false);

  const sortAzureGroups = (groups: AzureGroup[]) => {
    const sortedGroups = groups.sort((a, b) => {
      if (a.azure_group_name > b.azure_group_name) return 1;
      if (a.azure_group_name < b.azure_group_name) return -1;
      return 0;
    });

    return sortedGroups;
  };

  const groupHasPermission = (groupID: number, groupList: AzureGroup[]) => {
    return groupList.some((group) => group.azure_group_id == groupID);
  };

  const getAllUpdatedPermissions = (
    checked: boolean,
    permissionID: number,
    groupID: number,
  ) => {
    // 1. Build new current permissions
    const currentIndex = azurePermissions.current.findIndex(
      (el) => el.azure_permission_id === permissionID,
    );

    // Deep copy current permissions. Spread operator only provides a shallow copy
    // so nested elements get mutated. We do not want to mutate the state.
    let currentPermissions = JSON.parse(
      JSON.stringify(azurePermissions.current),
    );
    let currentPermissionToUpdate = JSON.parse(
      JSON.stringify(azurePermissions.current[currentIndex]),
    );

    // Checked - Add the group to the permission
    if (checked) {
      const group = azureGroups.find(
        (group) => group.azure_group_id === groupID,
      );
      if (group) {
        currentPermissionToUpdate.groups.push(group);
      }
    }

    // Unchecked - Remove the group from the permission
    else {
      currentPermissionToUpdate.groups = azurePermissions.current[
        currentIndex
      ].groups.filter((group) => group.azure_group_id !== groupID);
    }

    // Update the permission with the updated groups
    currentPermissions[currentIndex] = currentPermissionToUpdate;

    // 2. Build new updated permissions
    const updatedIndex = azurePermissions.updated.findIndex(
      (el) => el.azure_permission_id === permissionID,
    );

    // Deep copy updated permissions like we did current permissions above.
    let updatedPermissions = JSON.parse(
      JSON.stringify(azurePermissions.updated),
    );
    let updatedPermissionToUpdate =
      updatedIndex !== -1
        ? JSON.parse(JSON.stringify(azurePermissions.updated[updatedIndex]))
        : null;

    // Already exists in updated so just update
    if (updatedPermissionToUpdate) {
      updatedPermissions[updatedIndex] = currentPermissionToUpdate;
    }

    // Doesn't exist in updated yet so we'll add it
    else {
      updatedPermissions.push(currentPermissionToUpdate);
    }

    // Remove updated permission if it matches the original.
    // This means that nothing has actually changed so we'd
    // be passing a "false" update to the API.
    // Order of keys matters so we'll sort each group first
    const sortGroups = (a: AzureGroup, b: AzureGroup) => {
      if (a.azure_group_id > b.azure_group_id) return 1;
      if (a.azure_group_id < b.azure_group_id) return -1;
      return 0;
    };

    if (updatedPermissionToUpdate) {
      // Compare the groups and remove permission from updated if they match
      const originalGroups =
        azurePermissions.original[currentIndex].groups.sort(sortGroups);
      const updatedGroups =
        updatedPermissions[updatedIndex].groups.sort(sortGroups);

      if (isEqual(originalGroups, updatedGroups)) {
        updatedPermissions.splice(updatedIndex, 1);
      }
    }

    // 3. Return all updated permissions
    return {
      current: currentPermissions,
      updated: updatedPermissions,
    };
  };

  const handlePermissionChange = (
    e: React.ChangeEvent<HTMLInputElement>,
    permissionID: number,
    groupID: number,
  ) => {
    // Update state
    const updatedPermissions = getAllUpdatedPermissions(
      e.target.checked,
      permissionID,
      groupID,
    );

    setAzurePermissions({
      ...azurePermissions,
      current: updatedPermissions.current,
      updated: updatedPermissions.updated,
    });
  };

  const handleSettingsCancel = (e: React.MouseEvent) => {
    e.preventDefault();

    // Update state
    setAzurePermissions({
      ...azurePermissions,
      current: azurePermissions.original,
      updated: [],
    });
  };

  const handleSettingsSave = async (e: React.MouseEvent) => {
    e.preventDefault();
    if (azurePermissions.updated.length !== 0) {
      setSaved(true);

      setAzurePermissions({
        ...azurePermissions,
        original: [...azurePermissions.current],
        updated: [],
      });

      // Send updatedPermissions to API
      /* @todo: Uncomment and refactor when API is functional
      Permissions(updatedPermissions).then(() => {
        setAzurePermissions({
          ...azurePermissions,
          original: [...azurePermissions.current],
          updated: [],
        });
      });
      */
    }
  };

  useEffect(() => {
    // @todo: Remove when API is functional
    setAzurePermissions({
      current: getAzurePermissions,
      original: getAzurePermissions,
      updated: [],
    });

    // @todo: Remove when API is functional
    const mockGroups = sortAzureGroups(getAzureGroups);
    setAzureGroups(mockGroups);

    /* @todo: Uncomment and refactor when API is functional
    getAzurePermissions().then(
      (response: ApiResponse<PermissionsResponse>) => {
        setAzurePermissions({
          current: response.data,
          original: response.data,
          updated: [],
        });
      },
    );
    */

    /* @todo: Uncomment and refactor when API is functional
    getAzureGroups().then(
      (response: ApiResponse<AzureGroupsResponse>) => {
        setAzureGroups(sortAzureGroups(response.data));
      },
    );
    */

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <Helmet>
        <title>Settings</title>
      </Helmet>
      <h1>Settings</h1>
      {saved && (
        <Alert type="success" closeable={true} onClose={() => setSaved(false)}>
          Changes to Settings have been saved.
        </Alert>
      )}
      {error && (
        <Alert type="error" closeable={true} onClose={() => setError(false)}>
          An error occured when saving Settings.
        </Alert>
      )}
      {/* @todo Finish when authentication is functional
        <Alert type="info">View-only. Contact an ADMIN to configure these permissions.</Alert>
      */}
      <table className="table settings-table" cellPadding="0" cellSpacing="0">
        <thead>
          <tr className="table__head">
            <th key={0} className="table__header settings-table__header">
              Permissions
            </th>
            {azureGroups.map((group, index) => (
              <th
                key={index + 1}
                className="table__header settings-table__header settings-table__header--center"
              >
                {group.azure_group_name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="table__body">
          {azurePermissions.current.map((permission, trIndex) => {
            const groupPermissionTableCells: JSX.Element[] = [];

            // Loop over the azureGroups and get field value that way to ensure
            // the correct value is set for the correct column
            azureGroups.forEach((group, index) => {
              groupPermissionTableCells.push(
                <td
                  key={index + 1}
                  className="table__col settings-table__col settings-table__col--center"
                >
                  <input
                    type="checkbox"
                    className="settings-checkbox"
                    checked={groupHasPermission(
                      group.azure_group_id,
                      permission.groups,
                    )}
                    onChange={(e) => {
                      handlePermissionChange(
                        e,
                        permission.azure_permission_id,
                        group.azure_group_id,
                      );
                    }}
                  />
                </td>,
              );
            });

            return (
              <tr key={trIndex}>
                <td key={0} className="table__col settings-table__col">
                  {permission.azure_permission_name}
                </td>
                {groupPermissionTableCells}
              </tr>
            );
          })}
          <tr key={azurePermissions.current.length}>
            <td
              colSpan={azureGroups.length + 1}
              className="table__col settings-table__col"
            >
              <div className="settings-table__controls">
                <Button
                  disabled={
                    azurePermissions.updated.length === 0 ? true : false
                  }
                  className={"btn--cancel settings-btn settings-btn__cancel"}
                  onClick={handleSettingsCancel}
                >
                  Cancel
                </Button>
                <Button
                  disabled={
                    azurePermissions.updated.length === 0 ? true : false
                  }
                  className={"settings-btn settings-btn__save"}
                  onClick={handleSettingsSave}
                >
                  Save
                </Button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </>
  );
}
