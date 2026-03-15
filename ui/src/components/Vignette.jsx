
/**
 * A vignette overlay
 */
function Vignette({ children, colour = "rgb(0,0,0)" }) {
    return (
        <div className="relative flex flex-col h-full w-full z-40">
            {children}
            <div
                className="absolute inset-0 z-50"
                style={{
                    background: `radial-gradient(ellipse at center, transparent 65%, ${colour} 100%)`
                }}
            />
        </div>
    );
}

export default Vignette