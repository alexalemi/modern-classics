-- Byrne capture: serialise every paragraph as TeX typesets it, with each
-- picture box tagged by attribute 4242 = its capture number. See ../prep.py.
byc = byc or {}
local ATTR = 4242
byc.n = 0
byc.inmp = 0
local out = io.open("paragraphs.jsonl", "w")
local GLYPH, GLUE, HLIST, VLIST, RULE, KERN, MATH, DISC, PENALTY =
  node.id("glyph"), node.id("glue"), node.id("hlist"), node.id("vlist"),
  node.id("rule"), node.id("kern"), node.id("math"), node.id("disc"), node.id("penalty")

local function esc(s)
  s = s:gsub('\\','\\\\'):gsub('"','\\"')
  return (s:gsub('%c', function(c) return string.format('\\u%04x', c:byte()) end))
end

-- a glyph's own code may be private-use (ligatures, old-style figures,
-- swash forms): recover its text from the font's tounicode / unicode fields
local ucache = {}
function byc.unicode(f, c)
  local key = f * 0x200000 + c
  if ucache[key] then return ucache[key] end
  local s
  local fd = font.getfont(f)
  local ch = fd and fd.characters and fd.characters[c]
  if ch then
    local tu = ch.tounicode
    if type(tu) == "string" and #tu >= 4 then
      local cps = {}
      for i = 1, #tu, 4 do cps[#cps+1] = utf8.char(tonumber(tu:sub(i, i+3), 16)) end
      s = table.concat(cps)
    elseif type(ch.unicode) == "number" then s = utf8.char(ch.unicode)
    elseif type(ch.unicode) == "table" then
      local cps = {}
      for _, u in ipairs(ch.unicode) do cps[#cps+1] = utf8.char(u) end
      s = table.concat(cps)
    end
  end
  if not s and fd and (fd.encodingbytes == 1 or (fd.name or ""):match("^cm") or (fd.name or ""):match("^ms") or (fd.name or ""):match("oml")) then
    s = string.format("\u{27E8}%s:%d\u{27E9}", fd.name or "?", c)
  end
  if not s then
    if c >= 0xE000 and c <= 0xF8FF or c >= 0xF0000 then s = "\u{FFFD}" else s = utf8.char(c) end
  end
  ucache[key] = s
  return s
end

local function fontinfo(f)
  local fd = font.getfont(f)
  if not fd then return "?", 0 end
  return (fd.fullname or fd.name or "?"), (fd.size or 0)
end

-- items: {"t", text, fontname, size} | {"p", n} | {"frac", num, den} | {"stack", rows} | {"br"}
local function walk(head, items)
  for n in node.traverse(head) do
    local id = n.id
    local a = node.get_attribute(n, ATTR)
    if (id == HLIST or id == VLIST) and a then
      items[#items+1] = {"p", a}
    elseif id == GLYPH then
      local fname, size = fontinfo(n.font)
      local s = byc.unicode(n.font, n.char)
      local last = items[#items]
      if last and last[1] == "t" and last[3] == fname and last[4] == size then
        last[2] = last[2] .. s
      else
        items[#items+1] = {"t", s, fname, size}
      end
    elseif id == GLUE then
      local w = n.width or 0
      if w > 0 then
        local last = items[#items]
        if last and last[1] == "t" then last[2] = last[2] .. " "
        else items[#items+1] = {"t", " ", "", 0} end
      end
    elseif id == DISC then
      if n.replace then walk(n.replace, items) end
    elseif id == HLIST then
      if n.head then walk(n.head, items) end
    elseif id == VLIST then
      -- a vertical stack inside a line: a fraction (with a rule) or a stack
      local rows, hasrule = {}, false
      for m in node.traverse(n.head) do
        if m.id == RULE then hasrule = true
        elseif m.id == HLIST or m.id == VLIST then
          local sub = {}
          local ma = node.get_attribute(m, ATTR)
          if ma then sub[1] = {"p", ma} else walk(m.head, sub) end
          rows[#rows+1] = sub
        end
      end
      if hasrule and #rows == 2 then items[#items+1] = {"frac", rows[1], rows[2]}
      elseif #rows == 1 then for _, it in ipairs(rows[1]) do items[#items+1] = it end
      elseif #rows > 1 then items[#items+1] = {"stack", rows} end
    end
  end
end

local function dump(items)
  local parts = {}
  for _, it in ipairs(items) do
    if it[1] == "t" then
      parts[#parts+1] = string.format('["t","%s","%s",%d]', esc(it[2]), esc(it[3]), it[4])
    elseif it[1] == "p" then
      parts[#parts+1] = string.format('["p",%d]', it[2])
    elseif it[1] == "frac" then
      parts[#parts+1] = string.format('["frac",%s,%s]', dump(it[2]), dump(it[3]))
    elseif it[1] == "stack" then
      local rs = {}
      for _, r in ipairs(it[2]) do rs[#rs+1] = dump(r) end
      parts[#parts+1] = '["stack",[' .. table.concat(rs, ",") .. ']]'
    elseif it[1] == "br" then
      parts[#parts+1] = '["br"]'
    end
  end
  return "[" .. table.concat(parts, ",") .. "]"
end

local function serialise(head, groupcode)
  -- running heads and folios are set inside the output routine: not text
  if status.output_active then return true end
  -- labels inside a MetaPost picture are typeset as TeX boxes while the
  -- picture is built: part of the picture, not text
  if byc.inmp > 0 then return true end
  local items = {}
  -- a \\ inside a paragraph is a penalty -10000 followed by glue: a line break
  for n in node.traverse(head) do
    if n.id == PENALTY and n.penalty <= -10000 and n.next then
      node.set_attribute(n.next, 4243, 1)
    end
  end
  local its = {}
  local function walk2(h)
    for n in node.traverse(h) do
      if n.id == GLUE and node.get_attribute(n, 4243) then its[#its+1] = {"br"} end
      local one = {}
      local save = n.next
      n.next = nil
      walk(n, one)
      n.next = save
      for _, x in ipairs(one) do
        local last = its[#its]
        if x[1] == "t" and last and last[1] == "t" and last[3] == x[3] and last[4] == x[4] then
          last[2] = last[2] .. x[2]
        else its[#its+1] = x end
      end
    end
  end
  walk2(head)
  out:write(string.format('{"g":"%s","page":%d,"items":%s}\n', groupcode or "", tex.count["c@page"] or 0, dump(its)))
  out:flush()
  return true
end

luatexbase.add_to_callback("pre_linebreak_filter", serialise, "byrne.capture")

-- DISPLAY MATH never reaches the line breaker: take it when the math list
-- has been converted, in the order TeX meets it
luatexbase.add_to_callback("post_mlist_to_hlist_filter", function(head, display_type, need_penalties)
  if display_type == "display" and not status.output_active and byc.inmp == 0 then
    serialise(head, "display")
  end
  return true
end, "byrne.display")

local names = io.open("pictures.tsv", "w")
function byc.mark(boxnum, name)
  byc.n = byc.n + 1
  local b = tex.box[boxnum]
  names:write(string.format("%d\t%s\t%d\t%d\t%d\n", byc.n, name or "", b.width, b.height, b.depth))
  names:flush()
  node.set_attribute(tex.box[boxnum], ATTR, byc.n)
  tex.count["bycapno"] = byc.n
end

function byc.event(kind, text)
  out:write(string.format('{"event":"%s","text":"%s","page":%d}\n', esc(kind), esc(text or ""), tex.count["c@page"] or 0))
  out:flush()
end

-- everything luamplib typesets while processing a figure belongs to it
local orig_process = luamplib.process_mplibcode
luamplib.process_mplibcode = function(...)
  byc.inmp = byc.inmp + 1
  local ok, a, b, c = pcall(orig_process, ...)
  byc.inmp = byc.inmp - 1
  if not ok then error(a) end
  return a, b, c
end
