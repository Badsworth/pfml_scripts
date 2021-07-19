import Search from "../components/Search";
import Table from "../components/Table";
import Tag from "../components/Tag";
import SlideOut from "../components/SlideOut";
import usePopup from "../hooks/usePopup";
import { Helmet } from "react-helmet-async";
import { useState } from "react";

type User = {
  name: string;
  email: string;
  type: string;
};

// @todo: remove when api can be queried for users
const tempUsers = [
  {
    name: "yep name1",
    email: "yep email1",
    type: "Employee",
  },
  {
    name: "yep name2",
    email: "yep email2",
    type: "Employee",
  },
  {
    name: "yep name3",
    email: "yep email3",
    type: "Employee",
  },
  {
    name: "yep name4",
    email: "yep email4",
    type: "Employee",
  },
  {
    name: "yep name5",
    email: "yep email5",
    type: "Employee",
  },
];

export default function UserLookup() {
  const [users, setUsers] = useState<User[]>([]);
  const quickView = usePopup<typeof SlideOut>({
    title: "Quick view",
  });

  const findUsers = async (searchTerm: string) => {
    return new Promise((resolve) =>
      resolve(tempUsers.filter((u) => u.name.includes(searchTerm))),
    );
  };

  const getUsersName = (u: User) => <>{u.name}</>;
  const getUsersEmail = (u: User) => <>{u.email}</>;
  const getUsersType = (u: User) => <Tag text={u.type} color="green" />;
  const getUsersOptions = (u: User) => (
    <>
      <button onClick={(e) => quickView.onOpen(e)}>Quick view</button> |&nbsp;
      <button>View account</button>
    </>
  );

  return (
    <>
      <Helmet>
        <title>User Lookup</title>
      </Helmet>
      <h1 className="page__title">User Lookup</h1>
      <SlideOut {...quickView}>
        <p>ok</p>
      </SlideOut>
      <Search search={findUsers} setResults={setUsers} />
      <Table
        rows={users}
        cols={[
          {
            title: "Name",
            width: "25%",
            content: getUsersName,
          },
          {
            title: "Email",
            width: "25%",
            content: getUsersEmail,
          },
          {
            title: "Type",
            width: "25%",
            content: getUsersType,
          },
          {
            title: "",
            align: "right",
            content: getUsersOptions,
          },
        ]}
        noResults={<p>No results found</p>}
      />
    </>
  );
}
