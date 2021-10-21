import Alert from "./Alert";
import Button from "./Button";
import React from "react";
import tracker from "../services/tracker";
import { withTranslation } from "../locales/i18n";

interface ErrorBoundaryProps {
  children: React.ReactNode;
  t: (...args: any[]) => any;
}

/**
 * Error boundaries are React class components that catch JavaScript errors anywhere
 * in their child component tree, log those errors, and display a fallback UI
 * instead of the component tree that crashed. Error boundaries catch errors
 * during rendering, in lifecycle methods, and in constructors of the whole
 * tree below them.
 * @see https://reactjs.org/docs/error-boundaries.html
 */
export class ErrorBoundary extends React.Component<ErrorBoundaryProps> {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  /**
   * Invoked after an error has been thrown by a descendant component. Responsible
   * for updating our component's state to trigger the display of our error UI.
   */
  static getDerivedStateFromError(_error: Error) {
    return { hasError: true };
  }

  /**
   * Invoked after an error has been thrown by a descendant component. Responsible
   * for tracking the error we caught.
   * @param errorInfo.componentStack - information about which component threw the error
   */
  componentDidCatch(
    error: Error,
    {
      componentStack,
    }: {
      componentStack: string;
    }
  ) {
    tracker.noticeError(error, { componentStack });
  }

  handleReloadClick = () => {
    window.location.reload();
  };

  render() {
    const { t } = this.props;

    // @ts-expect-error ts-migrate(2339) FIXME: Property 'hasError' does not exist on type 'Readon... Remove this comment to see the full error message
    if (this.state.hasError) {
      return (
        <Alert state="error">
          <p>{t("components.errorBoundary.message")}</p>
          <Button onClick={this.handleReloadClick}>
            {t("components.errorBoundary.reloadButton")}
          </Button>
        </Alert>
      );
    }

    return this.props.children;
  }
}

export default withTranslation()(ErrorBoundary);
