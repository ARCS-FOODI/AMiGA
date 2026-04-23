obs = obslua

-- Must match your Text source name in OBS
source_name = "Experiment Clock"

-- Set this to the date you want to be "Day 1"
-- Format: YYYY-MM-DD
START_DATE = "2026-01-20"

timer_interval = 1000
last_text = ""

local function parse_ymd(ymd)
    local y, m, d = string.match(ymd, "^(%d%d%d%d)%-(%d%d)%-(%d%d)$")
    if not y then return nil end
    return tonumber(y), tonumber(m), tonumber(d)
end

local function day_index_calendar()
    local y, m, d = parse_ymd(START_DATE)
    if not y then
        return nil, "START_DATE must be in YYYY-MM-DD format"
    end

    -- Normalize both dates to local midnight to avoid 24h/seconds issues
    local start_midnight = os.time({year=y, month=m, day=d, hour=0, min=0, sec=0})
    local now = os.date("*t")
    local today_midnight = os.time({year=now.year, month=now.month, day=now.day, hour=0, min=0, sec=0})

    local diff_seconds = today_midnight - start_midnight
    local diff_days = math.floor(diff_seconds / 86400)

    return diff_days + 1, nil  -- Day 1 on START_DATE
end

local function make_text()
    local day, err = day_index_calendar()
    if not day then
        return "Day ?\n" .. err
    end

    local date_line = os.date("%b %d")      -- Jan 20
    local time_line = os.date("%H:%M:%S")   -- 14:22:19

    return "Day " .. tostring(day) .. "\n" .. date_line .. "\n" .. time_line
end

function update_clock()
    local text = make_text()
    if text == last_text then return end

    local source = obs.obs_get_source_by_name(source_name)
    if source == nil then return end

    local settings = obs.obs_data_create()
    obs.obs_data_set_string(settings, "text", text)
    obs.obs_source_update(source, settings)

    obs.obs_data_release(settings)
    obs.obs_source_release(source)

    last_text = text
end

function script_description()
    return "Updates an existing text source with Day N (calendar-based), date, and time. Set START_DATE to define Day 1."
end

function script_load(settings)
    obs.timer_add(update_clock, timer_interval)
end

function script_unload()
    obs.timer_remove(update_clock)
end