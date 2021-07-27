import ConfirmationDialog from "../components/ConfirmationDialog";
import { Helmet } from "react-helmet-async";
import { useState } from "react";
import Button from "../components/Button";
import UserLookup from "./users";
import SlideOut, { Props as SlideOutProps } from "../components/SlideOut";
import usePopup from "../hooks/usePopup";

export default function Home() {
  const [showConfirmationDialog, setShowConfirmationDialog] = useState(false);
  const [showUserLookup, setShowUserLookup] = useState(false);

  const confirmationDialogCancelCallback = () => {
    setShowConfirmationDialog(false);
  };

  const confirmationDialogContinueCallback = () => {
    setShowConfirmationDialog(false);
  };

  const { SlideOutPopup, openSlideOut } = usePopup<SlideOutProps>(SlideOut);

  if (!SlideOutPopup || !openSlideOut) {
    throw "Popup was not initialized!";
  }

  return (
    <>
      <Helmet>
        <title>Dashboard</title>
      </Helmet>
      <h1>h1 HTML5 Kitchen Sink</h1>
      <Button callback={() => setShowConfirmationDialog(true)}>
        Click to Open Confirmation Dialog
      </Button>
      <Button callback={openSlideOut()}>Click to Open Slide Out</Button>
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
      <SlideOutPopup title="Enable Caring Leave Type">
        <>
          <h2>Slideout!!</h2>
          <p>Lorem Ipsum stuff here...</p>
        </>
      </SlideOutPopup>
      {showUserLookup && <UserLookup />}
    </>
  );
}
