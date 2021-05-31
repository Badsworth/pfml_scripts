import React, { useEffect, useState } from "react";

// import Button from "../../components/Button";
// import Heading from "../../components/Heading";
// import InputChoice from "../../components/InputChoice";
// import InputDateTime from "../../components/InputDateTime";
// import InputText from "../../components/InputText";
// import Lead from "../../components/Lead";
import PropTypes from "prop-types";
import Table from "../../components/Table";
// import Title from "../../components/Title";
import User from "../../models/User";
// import { useTranslation } from "../../locales/i18n";
import withUser from "../../hoc/withUser";

export const Users = ({ appLogic }) => {
  // const { t } = useTranslation();

  const [users, setUsers] = useState([]);

  console.log(appLogic.users);
  useEffect(() => {
    appLogic.users.admin
      .getUsers()
      .then((allUsers) => setUsers(allUsers))
      .catch((e) => {
        throw e;
      });
  }, []);

  const sendEmailConvert = (user_id) => (e) => {
    e.preventDefault();
    appLogic.users.admin.convertUserToEmployer(user_id);
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
                  <button type="button" onClick={sendEmailConvert(u.user_id)}>
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
  // appLogic: PropTypes.instanceOf(User).isRequired,
};

export default withUser(Users);
