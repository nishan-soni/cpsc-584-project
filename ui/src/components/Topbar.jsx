import { act, useEffect, useState } from "react";

function Topbar({direction = "stopped", speed = "speed_normal"}) {
  const [now, setNow] = useState(new Date());

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
    <div className="flex flex-row absolute top-0 left-1/2 -translate-x-1/2 w-full justify-between items-center">
      <div className="p-2 bg-black/25 text-white font-mono">
        {formatted}
      </div>
      <div className="flex flex-row bg-black/25 justify-between items-center">
        <div className="p-2 bg-black/25 text-white font-mono">
          {direction}
        </div>
        <div className="p-2 bg-black/25 text-white font-mono">
          {speed}
        </div>
      </div>

    </div>
  );
}

export default Topbar;
