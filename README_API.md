# UFC Events API

A static API serving UFC event data for iOS apps.

## API Endpoints

- `GET /api/events/recent` - Returns the 20 most recent completed events
- `GET /api/events/upcoming` - Returns all upcoming events
- `GET /api/events/{event_id}` - Returns specific event details

## Data Structure

Events include:
- Event details (name, date, venue, location)
- Complete fight cards with results
- Fighter information
- Method and winner details (null for incomplete fights)

## Deployment

1. Push to GitHub
2. Connect to Vercel
3. Deploy automatically

The data folder contains 641 UFC events as static JSON files.

## Local Development

```bash
npm install -g vercel
vercel dev
```

Access at http://localhost:3000