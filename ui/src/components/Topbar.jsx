import { useEffect, useState } from "react";

function Topbar({direction = "stopped", speed = "speed_normal", took_photo = false}) {
  const [now, setNow] = useState(new Date());
  const panelClass = "p-2 bg-white/35 text-black backdrop-blur-md border border-white/50 rounded-xl shadow-[0_6px_20px_rgba(0,0,0,0.18)] font-mono";
  const groupClass = "flex flex-row gap-1 p-1 bg-white/35 text-black backdrop-blur-md border border-white/50 rounded-xl shadow-[0_6px_20px_rgba(0,0,0,0.18)]";

  useEffect(() => {
    const interval = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const formatted = now.toLocaleString("en-GB", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });

  return (
    <div className="flex flex-row absolute top-0 left-1/2 -translate-x-1/2 w-full justify-between items-center p-1">
      <div className={panelClass}>
        {formatted}
      </div>
      {took_photo &&
          <div className={groupClass}>
            <div className={panelClass}>
              photo taken
            </div>
          </div>
        }
      <div className={groupClass}>
        <div className={panelClass}>
          {direction}
        </div>
        <div className={panelClass}>
          {speed}
        </div>
      </div>

    </div>
  );
}

export default Topbar;
