# UFC Events Dashboard

A beautiful, responsive web interface for viewing UFC event data scraped by the UFC Scraper.

## 🎯 Features

### 📱 **Responsive Design**
- Beautiful gradient background with glass-morphism effects
- Fully responsive layout that works on desktop, tablet, and mobile
- Modern typography with Inter font family
- Smooth animations and hover effects

### 🔍 **Event Discovery**
- **Upcoming Events**: View scheduled UFC events
- **Recent Events**: Browse recently completed events  
- **All Events**: Complete event history
- **Search**: Find events by name, fighters, or venue
- **Filters**: Filter by year and event status

### 🥊 **Rich Event Details**
- **Event Cards**: Clean, card-based layout showing key event info
- **Main Event Preview**: Prominent display of main event fighters
- **Fight Status**: Visual indicators for scheduled vs completed events
- **Venue Information**: Location and venue details
- **Title Fight Indicators**: Special highlighting for championship bouts

### 📊 **Detailed Fight Information**
- **Complete Fight Cards**: Click any event to see all fights
- **Fighter Details**: Records, rankings, and countries
- **Fight Results**: Winners, methods, and round information
- **Weight Classes**: Organized by division
- **Title Fight Badges**: Clear championship indicators

### 🎨 **Visual Design**
- **Dark Theme**: Easy on the eyes with orange accent colors
- **Card-based Layout**: Clean, modern cards for each event
- **Status Badges**: Color-coded event and fight status
- **Smooth Transitions**: Polished animations and hover effects
- **Modal Popups**: Detailed event views in overlay windows

## 🚀 Quick Start

### Option 1: Easy Setup (Recommended)
```bash
python run_dashboard.py
```
Choose option 1 for quick start with sample data.

### Option 2: Manual Setup
```bash
# Start the web server
python web_server.py

# Open in browser
open http://localhost:8000
```

### Option 3: With Fresh Data
```bash
# First scrape some events
python scrape_ufc.py --mode recent --rate-limit 1.0

# Then start the dashboard
python web_server.py
```

## 📱 How to Use

### **Navigation**
- **Upcoming**: Shows future scheduled events
- **Recent**: Shows recently completed events
- **All Events**: Shows complete event history

### **Search & Filter**
- Use the search bar to find specific events, fighters, or venues
- Filter by year using the year dropdown
- Filter by status (scheduled/completed) using the status dropdown

### **Viewing Events**
- Events are displayed as cards with key information
- Click any event card to see the complete fight card
- Main events are prominently featured on each card
- Title fights are marked with crown icons

### **Event Details**
- Click any event to open detailed view
- See complete fight card with all bouts
- View fighter records and countries
- See fight results for completed events

## 🎨 Design Features

### **Color Scheme**
- Primary: Dark gradients (#1a1a2e to #16213e)
- Accent: Orange (#ff6b35)
- Text: White with various opacity levels
- Success: Green for wins and scheduled events
- Neutral: Gray for completed events

### **Typography**
- Font: Inter (Google Fonts)
- Weights: 300, 400, 500, 600, 700
- Responsive sizing for different screen sizes

### **Layout**
- CSS Grid for responsive event cards
- Flexbox for internal card layouts
- Backdrop filters for glass effects
- Smooth CSS transitions

## 🔧 Customization

### **Styling**
Edit `styles.css` to customize:
- Colors and gradients
- Typography and fonts  
- Layout and spacing
- Animations and effects

### **Data Display**
Edit `script.js` to customize:
- Event card content
- Search and filter logic
- Modal popup content
- Data formatting

### **API Integration**
The dashboard automatically:
- Tries to load from `/api/events` endpoint
- Falls back to built-in sample data
- Updates in real-time when new data is scraped

## 📊 Data Format

The dashboard expects events in this format:
```json
{
  "event_id": "ufc-305",
  "event_name": "UFC 305: Du Plessis vs Adesanya", 
  "event_date": "2024-08-17",
  "venue": "RAC Arena",
  "location": "Perth, Australia",
  "status": "completed",
  "fights": [
    {
      "bout_order": 1,
      "fighter1": {
        "name": "Dricus du Plessis",
        "record": "22-2-0",
        "country": "South Africa"
      },
      "fighter2": {
        "name": "Israel Adesanya", 
        "record": "24-3-0",
        "country": "Nigeria"
      },
      "weight_class": "Middleweight Championship",
      "title_fight": "undisputed",
      "winner": "Dricus du Plessis",
      "method": "Submission (R4 3:38)"
    }
  ]
}
```

## 🌐 API Endpoints

When running with `web_server.py`:

- `GET /api/events` - All events
- `GET /api/events/upcoming` - Upcoming events only
- `GET /api/events/recent` - Recent events only  
- `GET /api/events/{event_id}` - Specific event details

## 📱 Mobile Support

The dashboard is fully responsive:
- **Mobile**: Single column layout, larger touch targets
- **Tablet**: Two-column grid, optimized spacing
- **Desktop**: Multi-column grid, hover effects

## 🔍 Browser Support

Tested and working on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 🎯 Performance

- **Fast Loading**: Lightweight CSS and JavaScript
- **Efficient Rendering**: Virtual scrolling for large datasets
- **Optimized Images**: No heavy assets
- **Smooth Animations**: Hardware-accelerated CSS transitions

Enjoy exploring UFC events with this beautiful dashboard! 🥊