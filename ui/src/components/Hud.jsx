
import Controls from './Controls';
import Crosshair from './Crosshair'
import Topbar from './Topbar';
import Vignette from './Vignette'

import { useEffect, useRef, useState } from 'react';


const IMG_PATH = "http://172.17.10.217:9000/mjpg"

const VIGNETTE_COLORS = {
  GREEN: 'rgba(59, 178, 115, 0.4)',
  RED: 'rgba(225, 85, 84, 0.5)',
  NONE: 'rgba(0, 0, 0, 0)'
};


const DIRECTIONS = new Set(["stop", "forward", "back", "left", "right"]);

const SPEEDS = new Set(["speed_normal", "speed_sprint", "speed_ghost"]);

const TARGETS = new Set(["target_detected", "no_target"]);

const MENU = new Set(["open_menu", "close_menu"]);

const RECORDING = "toggle_record"

function Hud() {

    const [, setMessages] = useState([]);
    const [direction, setDirection] = useState("stopped")
    const [speed, setSpeed] = useState("speed_normal")
    const [enemy, setEnemy] = useState(false)
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

            if (MENU.has(incomingMessage)) {
                setMenu(incomingMessage)
            }

            if (incomingMessage === "toggle_record") {
                console.log("cam_t", !recording)
                setRecording(!recording)
            }

            if (TARGETS.has(incomingMessage)) {
                setEnemy(incomingMessage === "target_detected")
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
            <Vignette colour={enemy ? VIGNETTE_COLORS.RED : VIGNETTE_COLORS.NONE}>
                <Topbar direction={direction} speed={speed} took_photo = {tookPhoto} recording = {recording} enemy_detected = {enemy}/>
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