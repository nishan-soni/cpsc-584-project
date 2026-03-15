
import Crosshair from './Crosshair'
import Topbar from './Topbar';
import Vignette from './Vignette'


const IMG_PATH = "https://science.nasa.gov/wp-content/uploads/2023/09/stsci-01ga76rm0c11w977jrhgj5j26x-2.png?w=1024"

const VIGNETTE_COLORS = {
  GREEN: 'rgba(59, 178, 115, 0.4)',
  RED: 'rgba(225, 85, 84, 0.3)',
  NONE: 'rgba(0, 0, 0, 0)'
};

function Hud() {

    return (
        <div className="relative flex flex-col h-10/12 w-10/12 m-auto border-2">
            <Vignette colour={VIGNETTE_COLORS.GREEN}>
                <Topbar/>
                <Crosshair/>
                <img className="max-w-full max-h-full block" src={IMG_PATH} alt="Live Video"/>
            </Vignette>
        </div>
    )

}
 

export default Hud