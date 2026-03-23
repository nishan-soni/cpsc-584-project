/**
 * Crosshair overlay. To ensure it's in the center, we make it an absolutely positioned overlay that takes the full parent's size.
 */
function Crosshair() {
    return (
        <div className="absolute inset-0 flex flex-col justify-center items-center w-full h-full text-6xl z-50">
            <div className="w-1 h-10 bg-green-600 opacity-80" />
            <div className="w-10 h-1 bg-green-600 opacity-80 absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2" />
        </div>
    );
}

export default Crosshair