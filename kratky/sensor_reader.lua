obs = obslua

source_name = "Sensor Display"
file_path = "/home/foodi/Documents/AMiGA/kratky/sinfo"
interval = 2000 

function update_obs_text()
    local f = io.open(file_path, "r")
    if not f then return end
    local content = f:read("*all")
    f:close()

    local source = obs.obs_get_source_by_name(source_name)
    if source then
        local settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "text", content)
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)
    end
end

function script_load(settings)
    obs.timer_add(update_obs_text, interval)
end

function script_unload()
    obs.timer_remove(update_obs_text)
end