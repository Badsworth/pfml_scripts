import ConfirmationDialog from "../components/ConfirmationDialog";
import SlideOut from "../components/SlideOut";
import { Helmet } from "react-helmet-async";
import { useEffect, useState } from "react";
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

  const parseURLSearch = (search: string) => JSON.parse(
    '{"' +
      decodeURI(search)
        .replace(/"/g, '\\"')
        .replace(/&/g, '","')
        .replace(/=/g, '":"') +
      '"}',
  );

  useEffect(() => {
    if (!window.location.search) {
      fetch("http://localhost:1550/v1/admin/authorize", {
        headers: {
          Authorization:
            "Bearer "
        },
      })
        .then((r) => {
          return r.json();
        })
        .then((url) => {
          const queryArgs = parseURLSearch(url.split("?")[1]);
          localStorage.setItem("AzureADSSOAuthCode", JSON.stringify(queryArgs))
          window.location.href = url;
        });
    } else {
      const queryArgs = parseURLSearch(location.search.substring(1));
      const authCodeParams = JSON.parse(localStorage.getItem("AzureADSSOAuthCode") || "{}")
      console.log({ ...authCodeParams, ...queryArgs })
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
