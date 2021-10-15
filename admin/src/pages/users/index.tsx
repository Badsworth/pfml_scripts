import Search from "../../components/Search";
import Table from "../../components/Table";
import Tag from "../../components/Tag";
import Button from "../../components/Button";
import Alert from "../../components/Alert";
import SlideOut, { Props as SlideOutProps } from "../../components/SlideOut";
import usePopup from "../../hooks/usePopup";
import { Helmet } from "react-helmet-async";
import { useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";

type User = {
  id?: number;
  name: string;
  email: string;
  type: string;
  onSuppressionList: boolean;
  emailsBouncing: boolean;
  verifiedCognitoUser: boolean;
  emailDelivered: boolean;
};

// @todo: remove when api can be queried for users
export const tempUsers = [
  {
    id: 0,
    name: "yep name1",
    email: "yep email1",
    type: "Employee",
    onSuppressionList: false,
    emailsBouncing: false,
    verifiedCognitoUser: true,
    emailDelivered: true,
  },
  {
    id: 1,
    name: "yep name2",
    email: "yep email2",
    type: "Employee",
    onSuppressionList: false,
    emailsBouncing: false,
    verifiedCognitoUser: true,
    emailDelivered: true,
  },
  {
    id: 2,
    name: "yep name3",
    email: "yep email3",
    type: "Employee",
    onSuppressionList: false,
    emailsBouncing: false,
    verifiedCognitoUser: true,
    emailDelivered: true,
  },
  {
    id: 3,
    name: "yep name4",
    email: "yep email4",
    type: "Employee",
    onSuppressionList: false,
    emailsBouncing: false,
    verifiedCognitoUser: true,
    emailDelivered: true,
  },
  {
    id: 4,
    name: "yep name5",
    email: "yep email5",
    type: "Employee",
    onSuppressionList: false,
    emailsBouncing: false,
    verifiedCognitoUser: true,
    emailDelivered: true,
  },
];

export default function UserLookup() {
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const { Popup: SlideOutPopup, open: openSlideOut } = usePopup<
    SlideOutProps<User>,
    User
  >(SlideOut);

  const findUsers = async (searchTerm: string) => {
    return new Promise((resolve) => {
      resolve(tempUsers.filter((u) => u.name.includes(searchTerm)));
    });
  };

  const getUsersName = (u: User) => <>{u.name}</>;
  const getUsersEmail = (u: User) => <>{u.email}</>;
  const getUsersType = (u: User) => <Tag text={u.type} color="green" />;
  const getUsersOptions = (u: User) => (
    <>
      <Button className="btn--plain" onClick={openSlideOut(u)}>
        Quick view
      </Button>
      &nbsp; |&nbsp;
      <Link href={`/users/${u.id}`}>
        <a className="btn btn--plain">View account</a>
      </Link>
    </>
  );

  return (
    <>
      <Helmet>
        <title>User Lookup</title>
      </Helmet>
      <h1 className="page__title">User Lookup</h1>

      <SlideOutPopup title="Account Information">
        {(data: User) => {
          return (
            data && (
              <div className="slide-out--account-info">
                <div className="slide-out--account-info-image-wrapper">
                  <img
                    className="slide-out--account-info-image"
                    src="https://via.placeholder.com/32"
                    alt={data?.name}
                  />
                </div>
                <div className="slide-out--account-info-content-wrapper">
                  <div className="slide-out--account-info-header">
                    <div>
                      <p className="slide-out--account-info-name">
                        {data?.name}
                      </p>
                      <p className="slide-out--account-info-email">
                        {data?.email}
                      </p>
                    </div>

                    <div className="slide-out__tab-container">
                      <Tag text={data.type} color="green" />
                    </div>
                  </div>

                  <section className="slide-out__section">
                    <p className="slide-out__paragraph">
                      On the Suppression List?
                    </p>
                    {data.onSuppressionList ? "Yes" : "No"}
                  </section>

                  <section className="slide-out__section">
                    <p className="slide-out__paragraph">Emails Bouncing?</p>
                    {data.emailsBouncing ? "Yes" : "No"}
                  </section>

                  <section className="slide-out__section">
                    <p className="slide-out__paragraph">Cognito User?</p>
                    {data.verifiedCognitoUser ? "Yes" : "No"}
                  </section>

                  <section className="slide-out__section">
                    <p className="slide-out__paragraph">
                      Has an email been delivered?
                    </p>
                    {data.emailDelivered ? "Yes" : "No"}
                  </section>

                  <div className="slide-out--account-info-button-wrapper">
                    <Button
                      className="btn--blue btn--full-width slide-out--account-info-button"
                      onClick={() => {}}
                    >
                      View Account
                    </Button>
                  </div>
                </div>
              </div>
            )
          );
        }}
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
            align: "right",
            content: getUsersOptions,
          },
        ]}
        noResults={
          <div className="users__warning-wrapper">
            <Alert type="warn">
              No accounts found with that email address.
            </Alert>
          </div>
        }
      />
    </>
  );
}
