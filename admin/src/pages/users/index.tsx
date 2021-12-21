import Search from "../../components/Search";
import {
  ApiResponse,
  UserResponse,
  getAdminUsers,
  GETAdminUsersResponse,
} from "../../api";
import Table from "../../components/Table";
import Tag from "../../components/Tag";
import Button from "../../components/Button";
import Alert from "../../components/Alert";
import SlideOut, { Props as SlideOutProps } from "../../components/SlideOut";
import usePopup from "../../hooks/usePopup";
import { getAuthorizationHeader } from "../../utils/azure_sso_authorization";
import { Helmet } from "react-helmet-async";
import { useState } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import { StaticPropsPermissions } from "../../menus";

function UserLookup() {
  const router = useRouter();
  const [users, setUsers] = useState<UserResponse[]>([]);
  const { Popup: SlideOutPopup, open: openSlideOut } = usePopup<
    SlideOutProps<UserResponse>,
    UserResponse
  >(SlideOut);

  const findUsers = async (searchTerm: string) => {
    const returnedUsers = (
      await getAdminUsers(
        { email_address: searchTerm, page_size: 10 },
        { headers: await getAuthorizationHeader() },
      )
    ).data;
    setUsers(returnedUsers);
    return returnedUsers;
  };

  const getUsersName = (u: UserResponse) => {
    return [u?.first_name, u?.middle_name, u?.last_name].join(" ");
  };
  const getUsersEmail = (u: UserResponse) => <>{u.email_address}</>;
  const getUsersType = (u: UserResponse) => (
    <Tag text={"Employee"} color="green" />
  );
  const getUsersOptions = (u: UserResponse) => (
    <>
      <Button className="btn--plain" onClick={openSlideOut(u)}>
        Quick view
      </Button>
      &nbsp; |&nbsp;
      <Link href={`/users/${u.user_id}`}>
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
        {(data: UserResponse) => {
          return (
            data && (
              <div className="slide-out--account-info">
                <div className="slide-out--account-info-image-wrapper">
                  <img
                    className="slide-out--account-info-image"
                    src="https://via.placeholder.com/32"
                    alt={data?.last_name}
                  />
                </div>
                <div className="slide-out--account-info-content-wrapper">
                  <div className="slide-out--account-info-header">
                    <div>
                      <p className="slide-out--account-info-name">
                        {data?.last_name}
                      </p>
                      <p className="slide-out--account-info-email">
                        {data?.email_address}
                      </p>
                    </div>

                    <div className="slide-out__tab-container">
                      <Tag text={"employee"} color="green" />
                    </div>
                  </div>

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

// This function determines the list of permissions required
// to view this component, at a broad scale.
// If more accurate permission control is required,
// use the <HasPermission> component wrapper
export async function getStaticProps(): Promise<StaticPropsPermissions> {
  return {
    props: {
      permissions: ["USER_READ"],
    },
  };
}

export default UserLookup;
