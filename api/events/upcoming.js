import fs from 'fs';
import path from 'path';

export default function handler(req, res) {
  try {
    // Read all event files
    const dataDir = path.join(process.cwd(), 'data');
    const files = fs.readdirSync(dataDir);
    
    const events = [];
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    
    for (const file of files) {
      if (file.endsWith('.json')) {
        const filePath = path.join(dataDir, file);
        const eventData = JSON.parse(fs.readFileSync(filePath, 'utf8'));
        
        // Filter for upcoming events (scheduled events from today onwards)
        const eventDate = new Date(eventData.event_date);
        if (eventDate >= today) {
          events.push(eventData);
        }
      }
    }
    
    // Sort by date (soonest first)
    events.sort((a, b) => new Date(a.event_date) - new Date(b.event_date));
    
    res.status(200).json(events);
  } catch (error) {
    console.error('Error fetching upcoming events:', error);
    res.status(500).json({ error: 'Failed to fetch upcoming events' });
  }
}