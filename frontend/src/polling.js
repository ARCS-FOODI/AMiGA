export const POLL_INTERVALS = {
    FAST: 500,    // Scale Weight (feels interactive) - 2Hz
    NORMAL: 2000, // Environment sensors (Moisture, SIS, CO2, Light) - 0.5Hz
    STATUS: 2500, // Control status (Pumps, Recording, Recipe, Light flip)
    CHART: 5000   // Telemetry history charts refresh rate
};
