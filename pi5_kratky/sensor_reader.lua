obs = obslua

-- Environment source
env_source_name = "Environment Display"
env_file_path = "/home/foodi/Documents/AMiGA/kratky/sinfo_env.txt"

-- Water source
water_source_name = "Water Display"
water_file_path = "/home/foodi/Documents/AMiGA/kratky/sinfo_water.txt"

interval = 2000 

function update_obs_text_source(source_name, file_path)
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

function update_obs_text()
    update_obs_text_source(env_source_name, env_file_path)
    update_obs_text_source(water_source_name, water_file_path)
end

function script_load(settings)
    obs.timer_add(update_obs_text, interval)
end

function script_unload()
    obs.timer_remove(update_obs_text)
end