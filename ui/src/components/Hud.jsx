
import Controls from './Controls';
import Crosshair from './Crosshair'
import Topbar from './Topbar';
import Vignette from './Vignette'

import { useEffect, useRef, useState } from 'react';


const IMG_PATH = "http://172.17.10.217:9000/mjpg"
// const IMG_PATH = "http://192.168.1.97:9000/mjpg"
// const IMG_PATH = "https://cdn.pixabay.com/photo/2024/02/12/16/05/siguniang-mountain-8568913_1280.jpg"

const VIGNETTE_COLORS = {
  GREEN: 'rgba(59, 178, 115, 0.4)',
  RED: 'rgba(225, 85, 84, 0.3)',
  NONE: 'rgba(0, 0, 0, 0)'
};


const DIRECTIONS = new Set(["stop", "forward", "back", "left", "right"]);

const SPEEDS = new Set(["speed_normal", "speed_sprint", "speed_ghost"]);

// const LEAN = new Set(["look_up", "look_down", "lean_left", "lean_right"]);

const TARGETS = new Set(["target_detected", "no_target"]);

const MENU = new Set(["open_menu", "close_menu"]);

const RECORDING = "toggle_record"

function Hud() {

    const [, setMessages] = useState([]);
    const [direction, setDirection] = useState("stopped")
    const [speed, setSpeed] = useState("speed_normal")
    const [target, setTarget] = useState("no_target")
    const [menu, setMenu] = useState("close_menu")
    const [tookPhoto, setTookPhoto] = useState(false)
    const tookPhotoTimeoutRef = useRef(null)
    const [recording, setRecording] = useState(false)

    useEffect(() => {
        const socket = new WebSocket("ws://localhost:8765");

        socket.onopen = () => console.log("Connected");

        socket.onmessage = (event) => {

            const incomingMessage = String(event.data).trim();

            if (incomingMessage === "take_photo") {
                setTookPhoto(true)
                if (tookPhotoTimeoutRef.current) {
                    clearTimeout(tookPhotoTimeoutRef.current)
                }
                tookPhotoTimeoutRef.current = setTimeout(() => {
                    setTookPhoto(false)
                    tookPhotoTimeoutRef.current = null
                }, 1000)
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

            if (MENU.has(incomingMessage)) {
                setMenu(incomingMessage)
            }

            if (incomingMessage === "toggle_record") {
                console.log("cam_t", !recording)
                setRecording(!recording)
            }
            
            setMessages((prev) => [...prev, incomingMessage]);

        };
        socket.onclose = () => console.log("Disconnected");

        return () => {
            socket.close();
            if (tookPhotoTimeoutRef.current) {
                clearTimeout(tookPhotoTimeoutRef.current)
            }
        };
  }, [recording]);

    return (
        <div className="relative flex flex-col m-auto border-2">
            <Vignette colour={VIGNETTE_COLORS.NONE}>
                <Topbar direction={direction} speed={speed} took_photo = {tookPhoto} recording = {recording}/>
                <Crosshair/>
                <img className="max-w-full max-h-full block" src={IMG_PATH} alt="Live Video"/>
                {menu === "open_menu" &&
                    <Controls/>
                }
            </Vignette>
        </div>
    )

}
 

export default Hud