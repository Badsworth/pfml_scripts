import {
  ApiResponse,
  deleteRoles,
  RoleUserDeleteRequest,
  RequestOptions,
} from "../api";
import ConfirmationDialog from "../components/ConfirmationDialog";
import { Helmet } from "react-helmet-async";
import { useState } from "react";
import Button from "../components/Button";
import UserLookup from "./users";
import SlideOut, { Props as SlideOutProps } from "../components/SlideOut";
import usePopup from "../hooks/usePopup";
import { StaticPropsPermissions } from "../menus";

export default function Home() {
  const [showConfirmationDialog, setShowConfirmationDialog] = useState(false);
  const [showUserLookup, setShowUserLookup] = useState(false);

  const confirmationDialogCancelCallback = () => {
    setShowConfirmationDialog(false);
  };

  const confirmationDialogContinueCallback = () => {
    setShowConfirmationDialog(false);
    const request: RoleUserDeleteRequest = {
      role: {
        role_description: "Employer",
      },
      user_id: "b6d9222e-d5b5-416b-b252-c97725e81b3b",
    };
    deleteRoles(request).then().finally();
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
        Click to delete user role
      </Button>
      <Button onClick={openSlideOut()}>Click to Open Slide Out</Button>
      <Button onClick={() => setShowUserLookup(true)}>
        Click to Open User Lookup
      </Button>
      {showConfirmationDialog && (
        <ConfirmationDialog
          title="Delete user role"
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

export async function getStaticProps(): Promise<StaticPropsPermissions> {
  return {
    props: {
      permissions: ["USER_READ"],
    },
  };
}
