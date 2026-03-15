import { useEffect, useState } from "react";

function Topbar() {
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
    <div className="absolute top-0 left-1/2 -translate-x-1/2 p-2 bg-black/25 text-white font-mono">
        {formatted}
    </div>
    )
}

export default Topbar;