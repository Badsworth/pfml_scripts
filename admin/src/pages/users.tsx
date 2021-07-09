import Search from "../components/Search";
import Table from "../components/Table";
import { Helmet } from "react-helmet-async";
import { useState } from "react";

type User = {
  name: string;
  email: string;
};

export default function UserLookup() {
  const [users, setUsers] = useState<User[]>([
    {
      name: "yep name",
      email: "yep email",
    },
  ]);

  const findUsers = async (searchTerm: string) => {
    return new Promise((resolve) =>
      resolve([
        {
          name: "yep name2",
          email: "yep email2",
        },
      ]),
    );
  };

  const getUsersName = (u: User) => <>{u.name}</>;
  const getUsersEmail = (u: User) => <>{u.email}</>;
  const getUsersOptions = (u: User) => (
    <>
      <button>Quick view</button> |<button>View account</button>
    </>
  );

  return (
    <>
      <Helmet>
        <title>User Lookup</title>
      </Helmet>
      <h1>User Lookup</h1>
      <Search search={findUsers} setResults={setUsers} />
      <Table
        rows={users}
        rowData={[
          {
            title: "Name",
            content: getUsersName,
          },
          {
            title: "Email",
            content: getUsersEmail,
          },
          {
            title: "Options",
            content: getUsersOptions,
          },
        ]}
      />
    </>
  );
}
