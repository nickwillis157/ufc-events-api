import fs from 'fs';
import path from 'path';

export default function handler(req, res) {
    if (req.method !== 'GET') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        // Get pagination parameters
        const page = parseInt(req.query.page) || 1;
        const limit = parseInt(req.query.limit) || 20;
        const offset = (page - 1) * limit;

        // Get all JSON files from data directory
        const dataDir = path.join(process.cwd(), 'data');
        const files = [];
        
        for (const file of fs.readdirSync(dataDir)) {
            if (file.endsWith('.json')) {
                try {
                    const filePath = path.join(dataDir, file);
                    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
                    files.push(data);
                } catch (fileError) {
                    console.warn(`Skipping invalid JSON file: ${file}`, fileError.message);
                    continue;
                }
            }
        }

        // Filter for historical events (past events only)
        const today = new Date();
        today.setHours(0, 0, 0, 0); // Start of today
        
        const historicalEvents = files
            .filter(event => {
                const eventDate = new Date(event.event_date);
                return eventDate < today;
            })
            .sort((a, b) => new Date(b.event_date) - new Date(a.event_date)); // Sort by date descending (newest first)

        // Apply pagination
        const paginatedEvents = historicalEvents.slice(offset, offset + limit);
        
        // Return paginated response
        res.status(200).json({
            events: paginatedEvents,
            pagination: {
                page: page,
                limit: limit,
                total: historicalEvents.length,
                totalPages: Math.ceil(historicalEvents.length / limit),
                hasNext: offset + limit < historicalEvents.length,
                hasPrev: page > 1
            }
        });

    } catch (error) {
        console.error('Error fetching historical events:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
}