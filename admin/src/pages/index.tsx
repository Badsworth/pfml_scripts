import ConfirmationDialog from "../components/ConfirmationDialog";
import SlideOut from "../components/SlideOut";
import { Helmet } from "react-helmet-async";
import { Fragment, useEffect, useState } from "react";
import Button from "../components/Button";
import UserLookup from "./users";

export default function Home() {
  const [showConfirmationDialog, setShowConfirmationDialog] = useState(false);
  const [showSlideOut, setShowSlideOut] = useState(false);
  const [showUserLookup, setShowUserLookup] = useState(false);

  const confirmationDialogCancelCallback = () => {
    setShowConfirmationDialog(false);
  };

  const confirmationDialogContinueCallback = () => {
    setShowConfirmationDialog(false);
  };

  const slideOutCloseCallback = () => {
    setShowSlideOut(false);
  };

  const parseURLSearch = (search: string) =>
    JSON.parse(
      '{"' +
        decodeURI(search)
          .replace(/"/g, '\\"')
          .replace(/&/g, '","')
          .replace(/=/g, '":"') +
        '"}',
    );

  const headers = {
    "Content-Type": "application/json",
  };
  useEffect(() => {
    const ssoResponse = localStorage.getItem("SSOAuthorizationResponse");
    if (!window.location.search) {
      // get auth url
      fetch("http://localhost:1550/v1/admin/authorize", { headers })
        .then((r) => r.json())
        .then((res) => {
          const queryArgs = parseURLSearch(
            String(res["auth_uri"]).split("?")[1],
          );
          localStorage.setItem(
            "SSOAuthorizationResponse",
            JSON.stringify(res),
          );
          window.location.href = res["auth_uri"];
        });
    } else if (ssoResponse !== null) {
      // after it comes back from MS
      const authCodeRes = parseURLSearch(location.search.substring(1));
      const authCodeFlow = JSON.parse(ssoResponse);
      // localStorage.removeItem("SSOAuthorizationResponse");
      fetch("http://localhost:1550/v1/admin/login", {
        method: "POST",
        headers: {
          ...headers,
        },
        body: JSON.stringify({
          authCodeRes,
          authCodeFlow
        }),
      })
        .then((r) => r.json())
        .then((d) => console.log(d));
    }
  }, []);

  return (
    <>
      <Helmet>
        <title>Dashboard</title>
      </Helmet>
      <h1>h1 HTML5 Kitchen Sink</h1>
      <Button callback={() => setShowConfirmationDialog(true)}>
        Click to Open Confirmation Dialog
      </Button>
      <Button callback={() => setShowSlideOut(true)}>
        Click to Open Slide Out
      </Button>
      <Button callback={() => setShowUserLookup(true)}>
        Click to Open User Lookup
      </Button>
      {showConfirmationDialog && (
        <ConfirmationDialog
          title="Enable Caring Leave Type"
          body="Lorum ipsum"
          handleCancelCallback={confirmationDialogCancelCallback}
          handleContinueCallback={confirmationDialogContinueCallback}
        />
      )}
      {showSlideOut && (
        <SlideOut
          title="Enable Caring Leave Type"
          handleCloseCallback={slideOutCloseCallback}
        >
          <h2>Slideout!!</h2>
          <p>Lorem Ipsum stuff here...</p>
        </SlideOut>
      )}
      {showUserLookup && <UserLookup />}
    </>
  );
}
