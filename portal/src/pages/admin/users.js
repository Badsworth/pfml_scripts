import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import { RoleDescription } from "../../models/User";
import Table from "../../components/Table";
import withUser from "../../hoc/withUser";

export const Users = ({ appLogic }) => {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    appLogic.users.admin
      .getUsers()
      .then((allUsers) => setUsers(allUsers))
      .catch((e) => {
        throw e;
      });
  }, [appLogic.users.admin]);

  const sendAccountConversionEmail = (user_id, role) => (e) => {
    e.preventDefault();
    appLogic.users.admin.convertAccountEmail(user_id, role);
  };

  return (
    <Table>
      <caption>Users:</caption>
      <thead>
        <tr>
          <th scope="col">User ID</th>
          <th scope="col">Email</th>
          <th scope="col">Role</th>
          <th scope="col">Actions</th>
        </tr>
      </thead>
      <tbody>
        {users.length
          ? users.map((u) => (
              <tr key={u.user_id}>
                <td>{u.user_id}</td>
                <td>{u.email_address}</td>
                <td>
                  {u.roles.length
                    ? u.roles.map((r) => r.role_description).join(", ")
                    : ""}
                </td>
                <td>
                  <button
                    type="button"
                    onClick={sendAccountConversionEmail(
                      u.user_id,
                      RoleDescription.employer
                    )}
                  >
                    Convert to employer
                  </button>
                </td>
              </tr>
            ))
          : null}
      </tbody>
    </Table>
  );
};

Users.propTypes = {
  appLogic: PropTypes.shape({
    users: PropTypes.shape({
      admin: PropTypes.shape({
        getUsers: PropTypes.func.isRequired,
        convertAccountEmail: PropTypes.func.isRequired,
      }),
    }),
  }).isRequired,
};

export default withUser(Users);
