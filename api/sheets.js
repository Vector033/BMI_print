module.exports = async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const rawId = (req.query && req.query.id) ? String(req.query.id).trim() : '';
  if (!/^[a-zA-Z0-9_-]{10,120}$/.test(rawId)) {
    return res.status(400).json({ success: false, error: 'Invalid Google Sheet ID' });
  }

  try {
    const htmlUrl = `https://docs.google.com/spreadsheets/d/${rawId}/htmlview`;
    const response = await fetch(htmlUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    });

    if (!response.ok) {
      return res.status(response.status).json({
        success: false,
        error: `Google Sheets responded with HTTP ${response.status}`
      });
    }

    const html = await response.text();
    const tabs = [];
    const seen = new Set();

    // Pattern 1: items.push({name: "...", pageUrl: "...", gid: "..."})
    const regex1 = /items\.push\(\{name:\s*"((?:[^"\\]|\\.)*)",\s*pageUrl:[^}]+?gid:\s*"(\d+)"/g;
    let match;
    while ((match = regex1.exec(html)) !== null) {
      let name = match[1];
      try {
        name = JSON.parse(`"${name}"`);
      } catch (_) {}
      const gid = match[2];
      if (!seen.has(gid)) {
        seen.add(gid);
        tabs.push({ name, gid });
      }
    }

    // Fallback pattern if sheet has different structure
    if (tabs.length === 0) {
      const regex2 = /name:\s*"((?:[^"\\]|\\.)*)"[^}]{0,300}?gid:\s*"(\d+)"/g;
      while ((match = regex2.exec(html)) !== null) {
        let name = match[1];
        try {
          name = JSON.parse(`"${name}"`);
        } catch (_) {}
        const gid = match[2];
        if (!seen.has(gid)) {
          seen.add(gid);
          tabs.push({ name, gid });
        }
      }
    }

    res.setHeader('Cache-Control', 's-maxage=30, stale-while-revalidate=60');
    return res.status(200).json({ success: true, sheetId: rawId, tabs });
  } catch (err) {
    return res.status(500).json({ success: false, error: err.message || 'Failed to fetch tabs' });
  }
};
