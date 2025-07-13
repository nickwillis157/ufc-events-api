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
        
        // Filter for recent events (completed events from the past)
        const eventDate = new Date(eventData.event_date);
        if (eventDate < today && eventData.status === 'completed') {
          events.push(eventData);
        }
      }
    }
    
    // Sort by date (most recent first)
    events.sort((a, b) => new Date(b.event_date) - new Date(a.event_date));
    
    // Return top 20 recent events
    res.status(200).json(events.slice(0, 20));
  } catch (error) {
    console.error('Error fetching recent events:', error);
    res.status(500).json({ error: 'Failed to fetch recent events' });
  }
}