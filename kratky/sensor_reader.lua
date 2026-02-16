obs = obslua

-- CONFIGURATION
source_name = "Sensor Display"
file_path = "/home/foodi/Documents/AMiGA/kratky/sinfo"
update_interval = 2000 

function read_sensor_file(path)
    local file = io.open(path, "r")
    if not file then return "Searching for sinfo..." end
    local content = file:read("*all")
    file:close()
    return content
end

function update_sensor_text()
    local text = read_sensor_file(file_path)
    local source = obs.obs_get_source_by_name(source_name)
    
    if source ~= nil then
        local settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "text", text)
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)
    end
end

function script_description()
    return "Reads sensor data from " .. file_path
end

function script_load(settings)
    obs.timer_add(update_sensor_text, update_interval)
end

function script_unload()
    obs.timer_remove(update_sensor_text)
end