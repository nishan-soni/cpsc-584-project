
import Crosshair from './Crosshair'
import Topbar from './Topbar';
import Vignette from './Vignette'

import { useEffect, useState } from 'react';


// const IMG_PATH = "http://172.17.10.193:9000/mjpg"
const IMG_PATH = "https://science.nasa.gov/wp-content/uploads/2023/09/stsci-01ga76rm0c11w977jrhgj5j26x-2.png?w=1024"

const VIGNETTE_COLORS = {
  GREEN: 'rgba(59, 178, 115, 0.4)',
  RED: 'rgba(225, 85, 84, 0.3)',
  NONE: 'rgba(0, 0, 0, 0)'
};


const DIRECTIONS = new Set(["stop", "forward", "back", "left", "right"]);

const SPEEDS = new Set(["speed_normal", "speed_sprint", "speed_ghost"]);

const LEAN = new Set(["look_up", "look_down", "lean_left", "lean_right"]);

function Hud() {

    const [messages, setMessages] = useState([]);
    const [action, setAction] = useState("")
    const [recording, setRecording] = useState(false)
    const [direction, setDirection] = useState("stopped")
    const [speed, setSpeed] = useState("speed_normal")

    useEffect(() => {
        const socket = new WebSocket("ws://localhost:8765");

        socket.onopen = () => console.log("Connected");

        socket.onmessage = (event) => {

            const incomingMessage = String(event.data).trim();

            if (incomingMessage === "toggle_record") {
                setRecording(true)
                return
            }

            if (incomingMessage === "take_photo") {
                // do smth
                return
            }

            if (DIRECTIONS.has(incomingMessage)) {
                setDirection(incomingMessage)
            }

            if (SPEEDS.has(incomingMessage)) {
                setSpeed(incomingMessage)
            }

            // if (incomingMessage === "stop" || incomingMessage === "stand" || incomingMessage === "speed_normal" || incomingMessage === "cam_stop") {
            //     setAction("")
            //     return
            // }


            setAction(incomingMessage);
            
            setMessages((prev) => [...prev, incomingMessage]);

        };
        socket.onclose = () => console.log("Disconnected");

        return () => socket.close();
  }, []);

    return (
        <div className="relative flex flex-col m-auto border-2">
            <Vignette
                colour={
                    messages.at(-1) === 'enemy'
                        ? VIGNETTE_COLORS.RED
                        : messages.at(-1) === 'target'
                            ? VIGNETTE_COLORS.GREEN
                            : VIGNETTE_COLORS.NONE
                }
            >
                <Topbar direction={direction} speed={speed}/>
                <Crosshair/>
                <img className="max-w-full max-h-full block" src={IMG_PATH} alt="Live Video"/>
            </Vignette>
        </div>
    )

}
 

export default Hud