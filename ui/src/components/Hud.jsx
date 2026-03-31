
import Crosshair from './Crosshair'
import Topbar from './Topbar';
import Vignette from './Vignette'

import { useEffect, useState } from 'react';


// const IMG_PATH = "http://172.17.10.193:9000/mjpg"
const IMG_PATH = "http://192.168.1.97:9000/mjpg"

const VIGNETTE_COLORS = {
  GREEN: 'rgba(59, 178, 115, 0.4)',
  RED: 'rgba(225, 85, 84, 0.3)',
  NONE: 'rgba(0, 0, 0, 0)'
};


const DIRECTIONS = new Set(["stop", "forward", "back", "left", "right"]);

const SPEEDS = new Set(["speed_normal", "speed_sprint", "speed_ghost"]);

const LEAN = new Set(["look_up", "look_down", "lean_left", "lean_right"]);

const TARGETS = new Set(["target_detected", "no_target"]);

function Hud() {

    const [messages, setMessages] = useState([]);
    const [action, setAction] = useState("")
    const [recording, setRecording] = useState(false)
    const [direction, setDirection] = useState("stopped")
    const [speed, setSpeed] = useState("speed_normal")
    const [target, setTarget] = useState("no_target")

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

            if (TARGETS.has(incomingMessage)) {
                setTarget(incomingMessage)
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
            <Vignette colour={VIGNETTE_COLORS.RED ? target === "target_detected" : VIGNETTE_COLORS.NONE}>
                <Topbar direction={direction} speed={speed}/>
                <Crosshair/>
                <img className="max-w-full max-h-full block" src={IMG_PATH} alt="Live Video"/>
            </Vignette>
        </div>
    )

}
 

export default Hud