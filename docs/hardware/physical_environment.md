# Physical Environment & Hardware Rigging

The AMiGA platform operates within a highly confined, physical environment. Bringing the software and sensors into the real world required rapid mechanical problem-solving and rigorous spatial management. 

## The Grow Tent Enclosure
The entire biological system is contained within a closed **Vivosun Grow Tent** measuring **3 ft x 3 ft (square footprint) x 6 ft tall**. 
This provides the sealed climate necessary for academic environmental consistency but strictly limits the space available for sensitive recording hardware.

## The Custom Wooden AMiGA Rig (Rapid Prototyping)
Initially, we attempted to mount our controllers and trays using the provided tent mounting equipment and styrofoam boards. However, after extensive trial and error, the styrofoam proved structurally inadequate under the weight of the water and hardware, failing and collapsing twice. 

To solve this and stabilize the project, the team executed a rapid overnight build from hardware store supplies (wood and nails) to construct a custom, robust skeletal tower designed explicitly for the AMiGA trays:
- **Dimensions**: **2.5 ft x 2.5 ft x 3 ft tall**.
- **Tiered Structure**: Solid wooden mounting platforms are positioned at exactly every 1-foot vertical level to create stacked layers.

## Hardware Layout & Cable Routing
The tiered wooden framework inherently supports liquid isolation to protect the primary electronic controllers.

- **Upper Tiers (The Wet Zone)**: Holds the 10x10 grow trays, the 4-probe moisture sensor arrays planted directly into the soil, the peristaltic pumps, and all fluid tubing infrastructure.
- **Base Level (The Dry Zone)**: The Raspberry Pi 4 controller and core PCBs are situated securely on the very bottom platform, keeping them safely away from potential water spillage or high-moisture accumulation near the canopy.
- **Cable Management**: All primary power cables from the hardware are routed completely outside of the tent enclosure and connected to external power strips. This strictly isolates the high-voltage connections from the wet internal grow space, ensuring system safety and longevity.
