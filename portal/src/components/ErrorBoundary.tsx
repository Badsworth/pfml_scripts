import Alert from "./Alert";
import Button from "./Button";
import PropTypes from "prop-types";
import React from "react";
import tracker from "../services/tracker";
import { withTranslation } from "../locales/i18n";

/**
 * Error boundaries are React class components that catch JavaScript errors anywhere
 * in their child component tree, log those errors, and display a fallback UI
 * instead of the component tree that crashed. Error boundaries catch errors
 * during rendering, in lifecycle methods, and in constructors of the whole
 * tree below them.
 * @see https://reactjs.org/docs/error-boundaries.html
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  /**
   * Invoked after an error has been thrown by a descendant component. Responsible
   * for updating our component's state to trigger the display of our error UI.
   * @param {Error} _error
   * @returns {object} updated state
   */
  static getDerivedStateFromError(_error) {
    return { hasError: true };
  }

  /**
   * Invoked after an error has been thrown by a descendant component. Responsible
   * for tracking the error we caught.
   * @param {Error} error
   * @param {object} errorInfo
   * @param {string} errorInfo.componentStack - information about which component threw the error
   */
  componentDidCatch(error, { componentStack }) {
    tracker.noticeError(error, { componentStack });
  }

  handleReloadClick = () => {
    window.location.reload();
  };

  render() {
    // @ts-expect-error ts-migrate(2339) FIXME: Property 't' does not exist on type 'Readonly<{}> ... Remove this comment to see the full error message
    const { t } = this.props;

    // @ts-expect-error ts-migrate(2339) FIXME: Property 'hasError' does not exist on type 'Readon... Remove this comment to see the full error message
    if (this.state.hasError) {
      return (
        // @ts-expect-error ts-migrate(2322) FIXME: Type '{ children: Element[]; state: string; }' is ... Remove this comment to see the full error message
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

// @ts-expect-error ts-migrate(2339) FIXME: Property 'propTypes' does not exist on type 'typeo... Remove this comment to see the full error message
ErrorBoundary.propTypes = {
  children: PropTypes.node,
  /** Translate function */
  t: PropTypes.func.isRequired,
};

export default withTranslation()(ErrorBoundary);
