import ConfirmationDialog from "../components/ConfirmationDialog";
import SlideOut from "../components/SlideOut";
import { Helmet } from "react-helmet-async";
import { useState } from "react";
import Button from "../components/Button";

export default function Home() {
  const [showConfirmationDialog, setShowConfirmationDialog] = useState(false);
  const [showSlideOut, setShowSlideOut] = useState(false);

  const confirmationDialogCancelCallback = () => {
    setShowConfirmationDialog(false);
  };

  const confirmationDialogContinueCallback = () => {
    setShowConfirmationDialog(false);
  };

  const slideOutCloseCallback = () => {
    setShowSlideOut(false);
  };

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
    </>
  );
}
