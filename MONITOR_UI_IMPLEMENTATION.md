# Airport-Style Flight Monitor UI - Implementation Guide

**Repository**: This implementation belongs in https://github.com/jromie0924/plane-tracker-monitor-ui

## Overview

This document contains the complete implementation for a React Native mobile UI that displays tracked flights in an airport arrivals/departures monitor style. The application was designed with the following key features:

- Airport monitor-style display with customizable color themes
- Real-time or near real-time flight data updates
- Responsive layout for mobile devices (phones and tablets)
- Support for both Arrivals and Departures views
- Pub/sub architecture ready for AWS SNS/SQS or IoT Core integration

## Project Structure

```
plane-tracker-monitor-ui/
├── src/
│   ├── components/
│   │   ├── FlightBoard.tsx       # Main flight board container
│   │   ├── FlightRow.tsx          # Individual flight row component
│   │   └── FlightHeader.tsx       # Column headers
│   ├── types/
│   │   └── Flight.ts              # TypeScript type definitions
│   ├── themes/
│   │   └── themes.ts              # Color themes (5 pre-built themes)
│   ├── services/
│   │   └── MockFlightDataService.ts  # Mock data service with pub/sub pattern
│   └── App.tsx                    # Main application component
├── public/
│   └── index.html                 # HTML template for web build
├── index.js                       # React Native entry point
├── index.web.js                   # Web entry point
├── package.json                   # Dependencies and scripts
├── tsconfig.json                  # TypeScript configuration
├── webpack.config.js              # Webpack build configuration
└── README.md                      # Setup and usage instructions
```

## Technology Stack

- **React Native**: Cross-platform mobile development
- **TypeScript**: Type safety and better development experience
- **React Native Web**: Web browser support for development
- **Webpack**: Module bundler for web builds
- **Babel**: JavaScript transpilation

## Key Features

### 1. Customizable Themes

Five pre-built themes are included:

- **Airport Purple**: Default purple theme inspired by airport monitors
- **Airport Blue**: Bright blue alternative
- **Airport Green**: Green theme option
- **Dark**: Dark mode for night viewing
- **Light**: Light mode for daytime viewing

Each theme includes customizable colors for:
- Primary and secondary colors
- Background and surface colors
- Text colors (primary and secondary)
- Border colors
- Status colors (success, warning, error)
- Accent colors

### 2. Flight Data Model

Comprehensive flight information including:
- Flight identification (number, callsign)
- Airline information (name, ICAO, IATA codes)
- Aircraft details (registration, type)
- Location and routing (origin, destination, coordinates)
- Real-time position data (latitude, longitude, altitude, speed)
- Time information (departure, arrival, estimated times)
- Flight status (scheduled, boarding, departed, in_flight, landed, cancelled, delayed)

### 3. Pub/Sub Architecture

The `MockFlightDataService` implements a subscription pattern that can be easily replaced with:

- **AWS SNS + SQS**: For scalable pub/sub messaging
- **AWS IoT Core**: For MQTT real-time updates
- **WebSockets**: For self-hosted real-time connections
- **REST API**: For polling-based updates

The service provides:
- Subscribe/unsubscribe functionality
- Automatic periodic updates
- Start/stop controls
- Real-time notifications to all subscribers

### 4. Responsive Design

The UI automatically adapts to:
- Phone screens (portrait and landscape)
- Tablet screens
- Desktop browsers (for development)

## Implementation Files

### File: src/types/Flight.ts

Contains all TypeScript type definitions:
- `Flight` interface: Complete flight data structure
- `FlightView`: Type for 'arrivals' or 'departures'
- `FlightBoardConfig`: Configuration options for the board
- `ThemeColors`: Color palette definition
- `Theme`: Complete theme structure
- `ColumnConfig`: Column display configuration

### File: src/themes/themes.ts

Five complete theme definitions with:
- Color palettes for each theme
- Theme selection helper function
- TypeScript type safety for theme names

### File: src/services/MockFlightDataService.ts

Mock data service that:
- Generates realistic flight data
- Simulates real-time updates (altitude, speed, status changes)
- Implements pub/sub pattern
- Can be replaced with real data source

### File: src/components/FlightBoard.tsx

Main container component that:
- Displays flight list with auto-sort
- Shows current time and flight count
- Supports pull-to-refresh
- Handles empty state
- Updates every minute

### File: src/components/FlightRow.tsx

Individual flight display showing:
- Time (departure or arrival)
- Airline badge
- Flight number
- Route (origin → destination)
- Status with color coding
- Altitude and speed

### File: src/components/FlightHeader.tsx

Column headers with:
- Configurable visibility
- Responsive column widths
- Consistent styling with theme

### File: src/App.tsx

Main application with:
- Flight data subscription
- Theme switching
- View toggle (arrivals/departures)
- Control buttons
- State management

## Setup Instructions

### Prerequisites

- Node.js 14+ 
- npm or yarn
- For React Native mobile: React Native CLI setup

### Installation

```bash
# Clone the repository
git clone https://github.com/jromie0924/plane-tracker-monitor-ui.git
cd plane-tracker-monitor-ui

# Install dependencies
npm install

# For development dependencies
npm install --save-dev
```

### Development

```bash
# Start web development server
npm run start

# Build for production
npm run build

# Run on iOS (requires Mac and Xcode)
npm run ios

# Run on Android (requires Android Studio)
npm run android
```

### Required Dependencies

```json
{
  "dependencies": {
    "react": "^19.2.4",
    "react-native": "^0.84.0",
    "react-native-web": "^0.21.2"
  },
  "devDependencies": {
    "@types/react": "^19.2.14",
    "@types/react-native": "^0.72.8",
    "@typescript-eslint/eslint-plugin": "^8.55.0",
    "@typescript-eslint/parser": "^8.55.0",
    "eslint": "^9.39.2",
    "typescript": "^5.9.3",
    "webpack": "^5.x",
    "webpack-cli": "^5.x",
    "webpack-dev-server": "^4.x",
    "html-webpack-plugin": "^5.x",
    "@babel/core": "^7.x",
    "@babel/preset-react": "^7.x",
    "@babel/preset-typescript": "^7.x",
    "babel-loader": "^9.x",
    "ts-loader": "^9.x",
    "style-loader": "^3.x",
    "css-loader": "^6.x"
  }
}
```

## Integration with plane-tracker-rgb-pi

### Option 1: AWS Pub/Sub Architecture

The Python tracker can publish flight data to AWS SNS/SQS:

```python
# In plane-tracker-rgb-pi
import boto3
import json

sns_client = boto3.client('sns')
topic_arn = 'arn:aws:sns:region:account:flight-updates'

def publish_flight_update(flights):
    message = {
        'flights': flights,
        'timestamp': datetime.now().isoformat()
    }
    sns_client.publish(
        TopicArn=topic_arn,
        Message=json.dumps(message)
    )
```

The React Native app can subscribe via AWS SDK:

```typescript
import AWS from 'aws-sdk';

const sqs = new AWS.SQS();
const queueUrl = 'https://sqs.region.amazonaws.com/account/flight-updates';

async function pollFlightUpdates() {
    const messages = await sqs.receiveMessage({
        QueueUrl: queueUrl,
        MaxNumberOfMessages: 10,
        WaitTimeSeconds: 20
    }).promise();
    
    // Process flight updates
}
```

### Option 2: REST API

Expose an API endpoint from the tracker:

```python
# Flask example
@app.route('/api/flights')
def get_flights():
    return jsonify(get_nearby_flights())
```

Poll from React Native:

```typescript
async function fetchFlights() {
    const response = await fetch('http://tracker-ip:5000/api/flights');
    const flights = await response.json();
    return flights;
}
```

### Option 3: WebSocket

Real-time WebSocket connection:

```python
# Python WebSocket server
import asyncio
import websockets

async def flight_updates(websocket):
    while True:
        flights = get_nearby_flights()
        await websocket.send(json.dumps(flights))
        await asyncio.sleep(5)
```

```typescript
// React Native WebSocket client
const ws = new WebSocket('ws://tracker-ip:8080');
ws.onmessage = (event) => {
    const flights = JSON.parse(event.data);
    updateFlights(flights);
};
```

## Data Format

Flight data should be in the following JSON format:

```json
{
  "flights": [
    {
      "flightNumber": "AA1234",
      "callsign": "AAL1234",
      "airline": "American Airlines",
      "airlineIATA": "AA",
      "airlineICAO": "AAL",
      "registration": "N12345",
      "aircraftType": "B737",
      "origin": "Chicago O'Hare",
      "destination": "Los Angeles",
      "originIATA": "ORD",
      "destinationIATA": "LAX",
      "latitude": 41.9742,
      "longitude": -87.9073,
      "altitude": 35000,
      "altitudeMeters": 10668,
      "speed": 450,
      "speedKmh": 833,
      "heading": 270,
      "verticalRate": 0,
      "departureTime": "2026-02-14T10:30:00Z",
      "arrivalTime": "2026-02-14T14:45:00Z",
      "estimatedArrivalTime": "2026-02-14T14:42:00Z",
      "status": "in_flight",
      "distance": 25.5,
      "squawk": "1234",
      "isOnGround": false
    }
  ],
  "timestamp": "2026-02-14T20:30:00Z"
}
```

## AWS Cost Considerations

For pub/sub architecture using AWS:

### SNS + SQS Pricing
- First 1 million requests/month: FREE
- After 1 million: $0.50 per million requests
- For ~2 million messages/month: $0.50/month
- Data transfer: First 1GB free, then $0.09/GB

### IoT Core Pricing
- First 1 million messages/month: FREE  
- After 1 million: $1.00 per million messages
- Connection time: $0.08 per million minutes

For typical usage (updates every 5 seconds):
- 17,280 messages/day
- ~520,000 messages/month
- **Cost: $0 (under free tier)**

## Customization

### Adding a New Theme

```typescript
export const MyCustomTheme: Theme = {
  name: 'My Custom Theme',
  isDark: true,
  colors: {
    primary: '#YOUR_COLOR',
    secondary: '#YOUR_COLOR',
    background: '#YOUR_COLOR',
    surface: '#YOUR_COLOR',
    text: '#YOUR_COLOR',
    textSecondary: '#YOUR_COLOR',
    border: '#YOUR_COLOR',
    success: '#YOUR_COLOR',
    warning: '#YOUR_COLOR',
    error: '#YOUR_COLOR',
    accent: '#YOUR_COLOR',
  },
};

// Add to themes object
export const themes = {
  // ... existing themes
  myCustom: MyCustomTheme,
};
```

### Configuring Columns

Edit the `defaultColumns` array in `FlightBoard.tsx`:

```typescript
const defaultColumns: ColumnConfig[] = [
  { key: 'time', label: 'Time', width: 80, visible: true, sortable: true },
  { key: 'flightNumber', label: 'Flight', width: 120, visible: true, sortable: true },
  // Add or remove columns as needed
];
```

### Changing Update Frequency

In `App.tsx`, modify the service start interval:

```typescript
mockFlightService.start(10000); // Update every 10 seconds
```

## Future Enhancements

- [ ] Animated transitions for status changes
- [ ] Sound/alert for new or changed flights
- [ ] Airline logo display from assets
- [ ] Configurable column sorting by clicking headers
- [ ] Filter flights by airline, status, or route
- [ ] Save user preferences (theme, view, columns)
- [ ] Push notifications for flight status changes
- [ ] Historical flight data view
- [ ] Flight detail modal with more information
- [ ] Map view showing flight positions
- [ ] Export flight data to CSV
- [ ] Multi-language support

## Testing

### Manual Testing Checklist

- [ ] Verify arrivals view displays correctly
- [ ] Verify departures view displays correctly
- [ ] Test theme switching (all 5 themes)
- [ ] Test pull-to-refresh functionality
- [ ] Verify time updates every minute
- [ ] Check responsive layout on different screen sizes
- [ ] Verify status color coding
- [ ] Test empty state display
- [ ] Verify flight data updates in real-time

### Browser Testing

Open in browser: http://localhost:3000

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- Mobile browsers: Test responsive layout

## Troubleshooting

### Common Issues

**Issue**: "Cannot find module 'react-native'"
**Solution**: Run `npm install` to install dependencies

**Issue**: Webpack build errors
**Solution**: Clear cache and rebuild: `rm -rf node_modules dist && npm install && npm run build`

**Issue**: TypeScript errors
**Solution**: Check `tsconfig.json` configuration and ensure all type definitions are installed

**Issue**: Theme not applying
**Solution**: Verify theme name matches one in `themes.ts`

## License

MIT License - Same as plane-tracker-rgb-pi

## Credits

- Original plane-tracker-rgb-pi by @jromie0924
- Airport monitor UI concept inspired by real airport displays
- Built with React Native and TypeScript

---

**Last Updated**: February 14, 2026
