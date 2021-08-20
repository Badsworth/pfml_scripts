import Search from "../components/Search";
import Table from "../components/Table";
import Tag from "../components/Tag";
import Button from "../components/Button";
import Warning from "../components/Warning";
import SlideOut, { Props as SlideOutProps } from "../components/SlideOut";
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

  const { Popup: SlideOutPopup, open: openSlideOut } = usePopup<
    SlideOutProps<User>,
    User
  >(SlideOut);

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
      <Button additionalClasses={["btn--plain"]} onClick={openSlideOut(u)}>
        Quick view
      </Button>
      &nbsp; | &nbsp;
      <Button
        additionalClasses={["btn--plain"]}
        onClick={() => {
          //TODO link and pass state
        }}
      >
        View account
      </Button>
    </>
  );

  return (
    <>
      <Helmet>
        <title>User Lookup</title>
      </Helmet>
      <h1 className="page__title">User Lookup</h1>

      <SlideOutPopup title="Account Information">
        {(data) => (
          <>
            <div className="account-info-slideover__image-wrapper">
              <img alt="" src="https://via.placeholder.com/400" />
            </div>
            <p>{data?.name}</p>
            <p>{data?.email}</p>
            <p>{data?.type}</p>
          </>
        )}
      </SlideOutPopup>
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
        noResults={
          <div className="users__warning-wrapper">
            <Warning message="No accounts found with that email address." />
          </div>
        }
      />
    </>
  );
}
