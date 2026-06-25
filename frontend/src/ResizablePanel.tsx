import { useEffect, useRef, useState } from "react";

type Props = {
    initialWidth: number;
    minWidth: number;
    maxWidth: number;
    side: "left" | "right";
    children: React.ReactNode;
};

export default function ResizablePanel({
    initialWidth,
    minWidth,
    maxWidth,
    side,
    children
}: Props) {

    const [width, setWidth] = useState(initialWidth);

    const dragging = useRef(false);

    useEffect(() => {

        function mouseMove(e: MouseEvent) {

            if (!dragging.current)
                return;

            let next =
                side === "left"
                    ? e.clientX
                    : window.innerWidth - e.clientX;

            next = Math.max(minWidth, next);
            next = Math.min(maxWidth, next);

            setWidth(next);

        }

        function mouseUp() {
            dragging.current = false;
        }

        window.addEventListener("mousemove", mouseMove);
        window.addEventListener("mouseup", mouseUp);

        return () => {

            window.removeEventListener("mousemove", mouseMove);
            window.removeEventListener("mouseup", mouseUp);

        };

    }, [minWidth, maxWidth, side]);

    return (

        <div
            style={{
                width,
                display: "flex",
                position: "relative",
                overflow: "hidden",
                flexShrink: 0
            }}
        >

            {children}

            <div
                onMouseDown={() => {
                    dragging.current = true;
                }}
                style={{
                    position: "absolute",
                    top: 0,
                    bottom: 0,
                    right: side === "left" ? 0 : "auto",
                    left: side === "right" ? 0 : "auto",
                    width: 5,
                    cursor: "col-resize",
                    background: "transparent"
                }}
            />

        </div>

    );

}
