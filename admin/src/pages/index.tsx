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

  const { Popup: SlideOutPopup, open: openSlideOut } =
    usePopup<SlideOutProps>(SlideOut);

  return (
    <>
      <Helmet>
        <title>Dashboard</title>
      </Helmet>
      <h1>h1 HTML5 Kitchen Sink</h1>
      <Button onClick={() => setShowConfirmationDialog(true)}>
        Click to Open Confirmation Dialog
      </Button>
      <Button onClick={openSlideOut()}>Click to Open Slide Out</Button>
      <Button onClick={() => setShowUserLookup(true)}>
        Click to Open User Lookup
      </Button>
      {showConfirmationDialog && (
        <ConfirmationDialog
          title="Enable Caring Leave Type"
          body="Lorem ipsum, dolor sit amet consectetur adip elit. Eius aliquam laudantium explicabo pari dolorem."
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
