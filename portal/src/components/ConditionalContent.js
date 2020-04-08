import PropTypes from "prop-types";
import React from "react";

/**
 * Conditionally displays the content passed into it, and clears any
 * fields if they're hidden when the component unmounts. Based on
 * Vermont's Integrated Benefits `ConditionalContent` component.
 */
class ConditionalContent extends React.PureComponent {
  componentWillUnmount() {
    // Ensure all of the field values are cleared if they're not
    // visible when this component unmounts
    if (!this.props.visible && this.props.fieldNamesClearedWhenHidden) {
      this.props.fieldNamesClearedWhenHidden.forEach((name) => {
        this.props.removeField(name);
      });
    }
  }

  render() {
    if (!this.props.visible) return null;
    return this.props.children;
  }
}

ConditionalContent.propTypes = {
  /** Fields and other markup to be conditionally displayed */
  children: PropTypes.node.isRequired,
  /**
   * Field names, individually passed into `removeField` when the
   * content is hidden and this component unmounts
   */
  fieldNamesClearedWhenHidden: PropTypes.arrayOf(PropTypes.string),
  /**
   * Method called for each hidden field when the component unmounts.
   * In Redux, this is your bound action creator (meaning, calling this method
   * dispatches it).
   */
  removeField: PropTypes.func.isRequired,
  /** Should this component's children be visible? */
  visible: PropTypes.bool,
};

export default ConditionalContent;
