-- Course metadata shortcodes for TIE course detail pages
-- Generates content from YAML frontmatter to avoid duplication

local function stringify(val)
  if val == nil then return "" end
  return pandoc.utils.stringify(val)
end

local function fa_icon(name)
  return '<i class="fa-solid fa-' .. name .. '" aria-label="' .. name .. '"></i>'
end

local function escape_html(s)
  return s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"):gsub('"', "&quot;")
end

return {

  -- Generates the entire .pub-meta sidebar list from frontmatter
  -- Usage: {{< course-sidebar >}}
  ["course-sidebar"] = function(args, kwargs, meta)
    local html = '<div class="pub-meta">\n<ul>\n'

    -- ECTS
    if meta.ects then
      html = html .. '<li>' .. fa_icon("graduation-cap") .. ' '
        .. stringify(meta.ects) .. ' ECTS</li>\n'
    end

    -- Level
    if meta.level then
      html = html .. '<li>' .. fa_icon("layer-group") .. ' '
        .. escape_html(stringify(meta.level)) .. '</li>\n'
    end

    -- Semester
    if meta.semester then
      html = html .. '<li>' .. fa_icon("calendar") .. ' '
        .. escape_html(stringify(meta.semester)) .. '</li>\n'
    end

    -- Programs (comma-separated)
    if meta.programs then
      local prog_parts = {}
      for i = 1, #meta.programs do
        prog_parts[i] = escape_html(stringify(meta.programs[i]))
      end
      html = html .. '<li>' .. fa_icon("user-group") .. ' '
        .. table.concat(prog_parts, ", ") .. '</li>\n'
    end

    -- Registration URL
    if meta["registration-url"] then
      local url = escape_html(stringify(meta["registration-url"]))
      html = html .. '<li>' .. fa_icon("arrow-up-right-from-square")
        .. ' <a href="' .. url .. '">Registration (StudIP)</a></li>\n'
    end

    -- Course Website
    if meta["course-website"] then
      local url = escape_html(stringify(meta["course-website"]))
      html = html .. '<li>' .. fa_icon("arrow-up-right-from-square")
        .. ' <a href="' .. url .. '">Course Notes &amp; Materials</a></li>\n'
    end

    html = html .. '</ul>\n</div>'
    return pandoc.RawBlock('html', html)
  end,

  -- Generates instructor list with team profile links
  -- Usage: {{< course-instructors >}}
  ["course-instructors"] = function(args, kwargs, meta)
    if not meta or not meta.instructors then
      return pandoc.Null()
    end

    local md = ""
    for _, instructor in ipairs(meta.instructors) do
      local name = stringify(instructor.name)
      local internal = instructor.internal and stringify(instructor.internal) or nil
      if internal and internal ~= "" then
        md = md .. "- [" .. name .. "](/team/" .. internal .. "/)\n"
      else
        md = md .. "- " .. name .. "\n"
      end
    end

    return pandoc.read(md).blocks
  end,

  -- Generates time/location list with bold course names
  -- Usage: {{< course-timelocation >}}
  ["course-timelocation"] = function(args, kwargs, meta)
    if not meta or not meta["time-location"] then
      return pandoc.Null()
    end

    local md = ""
    for _, entry in ipairs(meta["time-location"]) do
      local text = stringify(entry)
      -- Split on first colon to bold the course name
      local colon_pos = text:find(":")
      if colon_pos then
        local name = text:sub(1, colon_pos - 1)
        local rest = text:sub(colon_pos)
        md = md .. "- **" .. name .. "**" .. rest .. "\n"
      else
        md = md .. "- " .. text .. "\n"
      end
    end

    return pandoc.read(md).blocks
  end,

}
