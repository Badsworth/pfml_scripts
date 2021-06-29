import { MouseEvent } from 'react';

type Props = {
    additionalClasses: string;
    callback: Function;
}

const Button= ({ additionalClasses = "", callback, children }: Props) => {
    const handleOnClick = (event: MouseEvent) => {
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
