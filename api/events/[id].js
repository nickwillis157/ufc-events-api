import fs from 'fs';
import path from 'path';

export default function handler(req, res) {
  try {
    const { id } = req.query;
    
    if (!id) {
      return res.status(400).json({ error: 'Event ID is required' });
    }
    
    // Try to find the event file
    const dataDir = path.join(process.cwd(), 'data');
    const filePath = path.join(dataDir, `${id}.json`);
    
    if (!fs.existsSync(filePath)) {
      return res.status(404).json({ error: 'Event not found' });
    }
    
    const eventData = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    res.status(200).json(eventData);
  } catch (error) {
    console.error('Error fetching event:', error);
    res.status(500).json({ error: 'Failed to fetch event' });
  }
}