import React from 'react';

type Props = {
    additionalClasses?: string;
    callback: Function;
    children: React.ReactNode;
}

const Button= ({ additionalClasses = "", callback, children }: Props) => {
    const handleOnClick = (event: React.MouseEvent) => {
        event.preventDefault();

        callback(event);
    }

    const classes = (additionalClasses.trim() == "") ? "" : " " + additionalClasses.trim();

    return (
        <button className={`btn${classes}`} onClick={handleOnClick}>
            <span className="btn__text">{children}</span>
        </button>
    );
};

export default Button;
