import { Helmet } from "react-helmet-async";
import { useRouter } from "next/router";

import Table from "../../components/Table";
import Tag from "../../components/Tag";
import ActionCard from "../../components/ActionCard";
import InfoRow, { Props as InfoRowProps } from "../../components/InfoRow";
import React from "react";
import Link from "next/link";
import isClient from "../../utils/isClient";

import { tempUsers } from "./index";

type AccountInfoRow = {
  title: string;
} & InfoRowProps;

export default function AccountInfo() {
  const router = useRouter();
  const user = tempUsers[Number(router.query.id)];

  const rows: AccountInfoRow[] = [
    {
      title: "Full Name",
      children: user.name,
      showLogButton: false,
    },
    {
      title: "Account Type",
      children: <Tag text={user.type} color="green" />,
      showLogButton: false,
    },
    {
      title: "Email",
      children: user.email,
      showLogButton: false,
    },
    {
      title: "On the Suppression List?",
      children: user.onSuppressionList ? "Yes" : "No",
      showLogButton: true,
      onClickViewLog: () => {},
    },
    {
      title: "Emails Bouncing?",
      children: user.emailsBouncing ? "Yes" : "No",
      showLogButton: true,
      onClickViewLog: () => {},
    },
    {
      title: "Verified Cognito User?",
      children: user.verifiedCognitoUser ? "Yes" : "No",
      showLogButton: true,
      onClickViewLog: () => {},
    },
    {
      title: "Has an email been delivered?",
      children: user.emailDelivered ? "Yes" : "No",
      showLogButton: true,
      onClickViewLog: () => {},
    },
  ];

  // @todo: on click handlers to send emails
  const onSendEmailConvertEmployeeToEmployer = () => {};
  const onSendEmailConvertEmployerToEmployee = () => {};
  // @todo: on click handlers to login as user
  const onLoginAsUser = () => {};

  let searchTerm: string | null = "";
  if (isClient()) {
    searchTerm = localStorage.getItem("user-search-term");
  }

  return (
    <>
      <Helmet>
        <title>Account Information</title>
      </Helmet>
      <Link href={`/users?search=${searchTerm}`}>
        <a className="btn--plain page__back-button">
          <i className="pfml-icon--arrow-1 page__back-icon"></i>
          Back to results
        </a>
      </Link>
      <h1 className="page__title">Account Information</h1>

      <Table<AccountInfoRow>
        hideHeaders={true}
        colClasses={"table__col--tall"}
        rows={rows}
        cols={[
          {
            width: "35%",
            content: (row) => row.title,
          },
          {
            width: "65%",
            content: InfoRow,
          },
        ]}
      />

      <ActionCard
        title="Convert Account"
        description="Send an email to the account holder with instructions on how to convert to an Employer account."
        buttonText="Send Email"
        onButtonClick={onSendEmailConvertEmployeeToEmployer}
      />

      <ActionCard
        title="Login as User"
        description="Login and view the portal through this user's account."
        buttonText="Login"
        onButtonClick={onLoginAsUser}
      />
    </>
  );
}
