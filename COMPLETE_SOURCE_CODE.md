# Complete TypeScript Source Code for plane-tracker-monitor-ui

This document contains all the **TypeScript** source code files for the airport-style flight monitor UI. 

## ✅ Full TypeScript Implementation

- **All components**: `.tsx` files (React with JSX)
- **All services/types**: `.ts` files (Pure TypeScript)
- **Strict mode enabled**: Maximum type safety
- **Complete type definitions**: Flight, Theme, and config types
- **Type-safe React components**: Strongly-typed props

Copy each section into the appropriate file in the new repository.

## Directory Structure

Create this structure in the plane-tracker-monitor-ui repository:

```
plane-tracker-monitor-ui/
├── src/
│   ├── components/
│   │   ├── FlightBoard.tsx
│   │   ├── FlightRow.tsx
│   │   └── FlightHeader.tsx
│   ├── types/
│   │   └── Flight.ts
│   ├── themes/
│   │   └── themes.ts
│   ├── services/
│   │   └── MockFlightDataService.ts
│   └── App.tsx
├── public/
│   └── index.html
├── index.js
├── index.web.js
├── package.json
├── tsconfig.json
├── webpack.config.js
├── .gitignore
└── README.md
```

---

## File: package.json

```json
{
  "name": "plane-tracker-monitor-ui",
  "version": "1.0.0",
  "description": "Airport-style flight monitor UI for tracking nearby aircraft",
  "main": "index.js",
  "scripts": {
    "start": "webpack serve --mode development",
    "build": "webpack --mode production",
    "android": "react-native run-android",
    "ios": "react-native run-ios",
    "lint": "eslint src --ext .ts,.tsx",
    "type-check": "tsc --noEmit"
  },
  "keywords": [
    "react-native",
    "flight-tracker",
    "airport-monitor",
    "adsb"
  ],
  "author": "jromie0924",
  "license": "MIT",
  "dependencies": {
    "react": "^19.2.4",
    "react-native": "^0.84.0",
    "react-native-web": "^0.21.2"
  },
  "devDependencies": {
    "@babel/core": "^7.26.0",
    "@babel/preset-react": "^7.26.0",
    "@babel/preset-typescript": "^7.26.0",
    "@types/react": "^19.2.14",
    "@types/react-native": "^0.72.8",
    "@typescript-eslint/eslint-plugin": "^8.55.0",
    "@typescript-eslint/parser": "^8.55.0",
    "babel-loader": "^9.2.1",
    "css-loader": "^6.11.0",
    "eslint": "^9.39.2",
    "html-webpack-plugin": "^5.6.3",
    "style-loader": "^3.3.4",
    "ts-loader": "^9.5.1",
    "typescript": "^5.9.3",
    "webpack": "^5.98.0",
    "webpack-cli": "^5.1.4",
    "webpack-dev-server": "^4.15.2"
  }
}
```

---

## File: tsconfig.json

```json
{
  "compilerOptions": {
    "target": "esnext",
    "module": "commonjs",
    "lib": ["esnext"],
    "jsx": "react-native",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "moduleResolution": "node",
    "allowSyntheticDefaultImports": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "isolatedModules": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules"]
}
```

---

## File: webpack.config.js

```javascript
const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  mode: 'development',
  entry: './index.web.js',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js',
  },
  module: {
    rules: [
      {
        test: /\.(ts|tsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'ts-loader',
        },
      },
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              '@babel/preset-react',
              '@babel/preset-typescript',
            ],
          },
        },
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'],
      },
    ],
  },
  resolve: {
    extensions: ['.web.js', '.js', '.web.ts', '.ts', '.web.tsx', '.tsx', '.json'],
    alias: {
      'react-native$': 'react-native-web',
    },
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: './public/index.html',
    }),
  ],
  devServer: {
    static: {
      directory: path.join(__dirname, 'public'),
    },
    compress: true,
    port: 3000,
    hot: true,
    open: true,
  },
};
```

---

## File: .gitignore

```
# Dependencies
node_modules/
.pnp
.pnp.js

# Testing
coverage/

# Production
dist/
build/

# Misc
.DS_Store
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Logs
npm-debug.log*
yarn-debug.log*
yarn-error.log*
*.log

# Editor
.vscode/
.idea/
*.swp
*.swo
*~

# React Native
.expo/
.expo-shared/

# TypeScript
*.tsbuildinfo

# Webpack
.cache/
```

---

## File: index.js

```javascript
import { AppRegistry } from 'react-native';
import App from './src/App';
import { name as appName } from './package.json';

AppRegistry.registerComponent(appName, () => App);
```

---

## File: index.web.js

```javascript
import { AppRegistry } from 'react-native';
import App from './src/App';

AppRegistry.registerComponent('PlaneTrackerMonitorUI', () => App);

AppRegistry.runApplication('PlaneTrackerMonitorUI', {
  rootTag: document.getElementById('root'),
});
```

---

## File: public/index.html

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Airport Flight Monitor</title>
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
        'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
        sans-serif;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }
    #root {
      width: 100%;
      height: 100vh;
      overflow: hidden;
    }
  </style>
</head>
<body>
  <div id="root"></div>
</body>
</html>
```

---

## File: src/types/Flight.ts

```typescript
/**
 * Flight data types for the airport-style monitor UI
 */

export interface Flight {
  // Flight identification
  flightNumber: string;
  callsign?: string;
  
  // Airline information
  airline?: string;
  airlineICAO?: string;
  airlineIATA?: string;
  
  // Aircraft information
  registration?: string;
  aircraftType?: string;
  
  // Location and routing
  origin?: string;
  destination?: string;
  originIATA?: string;
  destinationIATA?: string;
  
  // Position data
  latitude?: number;
  longitude?: number;
  altitude?: number; // feet
  altitudeMeters?: number;
  
  // Speed and heading
  speed?: number; // knots
  speedKmh?: number;
  heading?: number; // degrees
  verticalRate?: number; // feet per minute
  
  // Time information
  departureTime?: string;
  arrivalTime?: string;
  estimatedArrivalTime?: string;
  
  // Status
  status?: 'scheduled' | 'boarding' | 'departed' | 'in_flight' | 'landed' | 'cancelled' | 'delayed';
  
  // Additional data
  distance?: number; // distance from observer
  squawk?: string;
  isOnGround?: boolean;
}

export type FlightView = 'arrivals' | 'departures';

export interface FlightBoardConfig {
  view: FlightView;
  refreshInterval: number; // milliseconds
  maxFlights: number;
  sortBy: keyof Flight;
  sortOrder: 'asc' | 'desc';
}

export interface ThemeColors {
  primary: string;
  secondary: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  success: string;
  warning: string;
  error: string;
  accent: string;
}

export interface Theme {
  name: string;
  colors: ThemeColors;
  isDark: boolean;
}

export interface ColumnConfig {
  key: keyof Flight | 'time';
  label: string;
  width?: number | string;
  visible: boolean;
  sortable: boolean;
}
```

---

## File: src/themes/themes.ts

```typescript
import { Theme } from '../types/Flight';

/**
 * Default theme inspired by airport monitors (purple/blue)
 */
export const AirportPurpleTheme: Theme = {
  name: 'Airport Purple',
  isDark: true,
  colors: {
    primary: '#9D4EDD',      // Purple
    secondary: '#7B2CBF',    // Deep purple
    background: '#1A0B2E',   // Very dark purple
    surface: '#2E1A47',      // Dark purple surface
    text: '#FFFFFF',         // White text
    textSecondary: '#C9B8E8', // Light purple text
    border: '#5A2D8F',       // Purple border
    success: '#06D6A0',      // Green for arrived
    warning: '#FFD60A',      // Yellow for delayed
    error: '#EF476F',        // Red for cancelled
    accent: '#00D9FF',       // Cyan accent
  },
};

/**
 * Light mode theme for daytime viewing
 */
export const LightTheme: Theme = {
  name: 'Light',
  isDark: false,
  colors: {
    primary: '#1976D2',      // Blue
    secondary: '#1565C0',    // Dark blue
    background: '#F5F5F5',   // Light gray
    surface: '#FFFFFF',      // White
    text: '#212121',         // Dark text
    textSecondary: '#757575', // Gray text
    border: '#E0E0E0',       // Light border
    success: '#4CAF50',      // Green
    warning: '#FF9800',      // Orange
    error: '#F44336',        // Red
    accent: '#00BCD4',       // Cyan
  },
};

/**
 * Dark theme for night viewing
 */
export const DarkTheme: Theme = {
  name: 'Dark',
  isDark: true,
  colors: {
    primary: '#2196F3',      // Blue
    secondary: '#1976D2',    // Dark blue
    background: '#121212',   // Very dark gray
    surface: '#1E1E1E',      // Dark surface
    text: '#FFFFFF',         // White text
    textSecondary: '#AAAAAA', // Gray text
    border: '#333333',       // Dark border
    success: '#4CAF50',      // Green
    warning: '#FF9800',      // Orange
    error: '#F44336',        // Red
    accent: '#00BCD4',       // Cyan
  },
};

/**
 * Blue theme alternative
 */
export const AirportBlueTheme: Theme = {
  name: 'Airport Blue',
  isDark: true,
  colors: {
    primary: '#0096FF',      // Bright blue
    secondary: '#0077CC',    // Deep blue
    background: '#001F3F',   // Navy blue
    surface: '#003366',      // Dark blue surface
    text: '#FFFFFF',         // White text
    textSecondary: '#B3D9FF', // Light blue text
    border: '#004C99',       // Blue border
    success: '#06D6A0',      // Green
    warning: '#FFD60A',      // Yellow
    error: '#EF476F',        // Red
    accent: '#00D9FF',       // Cyan
  },
};

/**
 * Green theme alternative
 */
export const AirportGreenTheme: Theme = {
  name: 'Airport Green',
  isDark: true,
  colors: {
    primary: '#10B981',      // Green
    secondary: '#059669',    // Deep green
    background: '#064E3B',   // Dark green
    surface: '#065F46',      // Dark green surface
    text: '#FFFFFF',         // White text
    textSecondary: '#D1FAE5', // Light green text
    border: '#047857',       // Green border
    success: '#34D399',      // Light green
    warning: '#FBBF24',      // Yellow
    error: '#EF4444',        // Red
    accent: '#06B6D4',       // Cyan
  },
};

export const themes = {
  airportPurple: AirportPurpleTheme,
  airportBlue: AirportBlueTheme,
  airportGreen: AirportGreenTheme,
  light: LightTheme,
  dark: DarkTheme,
};

export type ThemeName = keyof typeof themes;

export const getTheme = (name: ThemeName): Theme => {
  return themes[name] || AirportPurpleTheme;
};
```

---

## File: src/services/MockFlightDataService.ts

```typescript
import { Flight } from '../types/Flight';

/**
 * Mock flight data service for development and testing
 * In production, this would be replaced with real API calls or pub/sub integration
 */

const airlines = [
  { iata: 'AA', icao: 'AAL', name: 'American Airlines' },
  { iata: 'UA', icao: 'UAL', name: 'United Airlines' },
  { iata: 'DL', icao: 'DAL', name: 'Delta Air Lines' },
  { iata: 'BA', icao: 'BAW', name: 'British Airways' },
  { iata: 'LH', icao: 'DLH', name: 'Lufthansa' },
  { iata: 'AF', icao: 'AFR', name: 'Air France' },
  { iata: 'QU', icao: 'QTR', name: 'Qatar Airways' },
  { iata: 'EK', icao: 'UAE', name: 'Emirates' },
  { iata: 'SQ', icao: 'SIA', name: 'Singapore Airlines' },
  { iata: 'TK', icao: 'THY', name: 'Turkish Airlines' },
];

const airports = [
  { iata: 'ORD', name: 'Chicago O\'Hare' },
  { iata: 'JFK', name: 'New York JFK' },
  { iata: 'LAX', name: 'Los Angeles' },
  { iata: 'LHR', name: 'London Heathrow' },
  { iata: 'CDG', name: 'Paris Charles de Gaulle' },
  { iata: 'FRA', name: 'Frankfurt' },
  { iata: 'DXB', name: 'Dubai' },
  { iata: 'SIN', name: 'Singapore' },
  { iata: 'IST', name: 'Istanbul' },
  { iata: 'DME', name: 'Moscow' },
];

const statuses: Flight['status'][] = [
  'scheduled',
  'boarding',
  'departed',
  'in_flight',
  'landed',
  'delayed',
];

const generateMockFlight = (index: number): Flight => {
  const airline = airlines[Math.floor(Math.random() * airlines.length)];
  const origin = airports[Math.floor(Math.random() * airports.length)];
  const destination = airports[Math.floor(Math.random() * airports.length)];
  const status = statuses[Math.floor(Math.random() * statuses.length)];
  
  const flightNumber = `${airline.iata}${1000 + Math.floor(Math.random() * 9000)}`;
  const altitude = Math.floor(Math.random() * 40000) + 5000;
  const speed = Math.floor(Math.random() * 300) + 300;
  
  const now = new Date();
  const departureTime = new Date(now.getTime() - Math.random() * 3 * 60 * 60 * 1000);
  const arrivalTime = new Date(departureTime.getTime() + Math.random() * 8 * 60 * 60 * 1000);
  
  return {
    flightNumber,
    callsign: `${airline.icao}${flightNumber.slice(2)}`,
    airline: airline.name,
    airlineIATA: airline.iata,
    airlineICAO: airline.icao,
    registration: `N${Math.floor(Math.random() * 10000)}`,
    aircraftType: 'B737',
    origin: origin.name,
    destination: destination.name,
    originIATA: origin.iata,
    destinationIATA: destination.iata,
    latitude: 41.9742 + (Math.random() - 0.5) * 2,
    longitude: -87.9073 + (Math.random() - 0.5) * 2,
    altitude,
    altitudeMeters: Math.round(altitude * 0.3048),
    speed,
    speedKmh: Math.round(speed * 1.852),
    heading: Math.floor(Math.random() * 360),
    verticalRate: Math.floor(Math.random() * 2000) - 1000,
    departureTime: departureTime.toISOString(),
    arrivalTime: arrivalTime.toISOString(),
    estimatedArrivalTime: new Date(arrivalTime.getTime() + (Math.random() - 0.5) * 30 * 60 * 1000).toISOString(),
    status,
    distance: Math.floor(Math.random() * 50) + 5,
    squawk: `${Math.floor(Math.random() * 10000)}`.padStart(4, '0'),
    isOnGround: status === 'landed' || status === 'boarding',
  };
};

/**
 * Generate mock flight data
 */
export const getMockFlights = (count: number = 10): Flight[] => {
  return Array.from({ length: count }, (_, i) => generateMockFlight(i));
};

/**
 * Mock service to simulate real-time flight data updates
 */
export class MockFlightDataService {
  private flights: Flight[] = [];
  private listeners: ((flights: Flight[]) => void)[] = [];
  private intervalId: NodeJS.Timeout | null = null;

  constructor(initialFlightCount: number = 15) {
    this.flights = getMockFlights(initialFlightCount);
  }

  /**
   * Start the mock data service with periodic updates
   */
  start(updateInterval: number = 5000): void {
    if (this.intervalId) {
      return; // Already started
    }

    // Notify listeners immediately with initial data
    this.notifyListeners();

    // Set up periodic updates
    this.intervalId = setInterval(() => {
      this.updateFlights();
    }, updateInterval);
  }

  /**
   * Stop the mock data service
   */
  stop(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  /**
   * Subscribe to flight data updates
   */
  subscribe(listener: (flights: Flight[]) => void): () => void {
    this.listeners.push(listener);
    
    // Return unsubscribe function
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  /**
   * Get current flights
   */
  getFlights(): Flight[] {
    return [...this.flights];
  }

  /**
   * Simulate flight data updates
   */
  private updateFlights(): void {
    // Randomly update some flight properties
    this.flights = this.flights.map(flight => {
      // Random chance to update altitude and speed
      if (Math.random() > 0.7) {
        const altitudeChange = (Math.random() - 0.5) * 1000;
        const newAltitude = Math.max(0, flight.altitude! + altitudeChange);
        
        return {
          ...flight,
          altitude: Math.round(newAltitude),
          altitudeMeters: Math.round(newAltitude * 0.3048),
          speed: Math.round(flight.speed! + (Math.random() - 0.5) * 20),
          verticalRate: Math.round(altitudeChange),
        };
      }
      
      // Random chance to update status
      if (Math.random() > 0.9 && flight.status !== 'landed') {
        const currentStatusIndex = statuses.indexOf(flight.status!);
        const newStatus = statuses[Math.min(currentStatusIndex + 1, statuses.length - 1)];
        return {
          ...flight,
          status: newStatus,
          isOnGround: newStatus === 'landed',
        };
      }
      
      return flight;
    });

    // Occasionally add a new flight or remove one
    if (Math.random() > 0.8 && this.flights.length < 20) {
      this.flights.push(generateMockFlight(this.flights.length));
    } else if (Math.random() > 0.9 && this.flights.length > 5) {
      this.flights.splice(Math.floor(Math.random() * this.flights.length), 1);
    }

    this.notifyListeners();
  }

  /**
   * Notify all listeners of flight data updates
   */
  private notifyListeners(): void {
    const flightsCopy = this.getFlights();
    this.listeners.forEach(listener => listener(flightsCopy));
  }
}

// Export singleton instance for easy use
export const mockFlightService = new MockFlightDataService();
```

---

## File: src/components/FlightHeader.tsx

```typescript
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Theme, ColumnConfig } from '../types/Flight';

interface FlightHeaderProps {
  columns: ColumnConfig[];
  theme: Theme;
}

/**
 * Header component for the flight board displaying column names
 */
export const FlightHeader: React.FC<FlightHeaderProps> = ({ columns, theme }) => {
  return (
    <View style={[styles.container, { backgroundColor: theme.colors.surface, borderColor: theme.colors.border }]}>
      {columns.filter(col => col.visible).map((column) => (
        <View
          key={column.key}
          style={[
            styles.column,
            column.width ? { width: column.width } : { flex: 1 },
          ]}
        >
          <Text style={[styles.headerText, { color: theme.colors.text }]}>
            {column.label}
          </Text>
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    paddingVertical: 16,
    paddingHorizontal: 12,
    borderBottomWidth: 2,
  },
  column: {
    paddingHorizontal: 8,
    justifyContent: 'center',
  },
  headerText: {
    fontSize: 14,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
});
```

---

## File: src/components/FlightRow.tsx

```typescript
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Flight, Theme } from '../types/Flight';

interface FlightRowProps {
  flight: Flight;
  theme: Theme;
  showAirline?: boolean;
  showStatus?: boolean;
}

/**
 * Individual flight row component displaying flight information
 */
export const FlightRow: React.FC<FlightRowProps> = ({
  flight,
  theme,
  showAirline = true,
  showStatus = true,
}) => {
  const formatTime = (dateString?: string): string => {
    if (!dateString) return '--:--';
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  };

  const getStatusColor = (status?: string): string => {
    switch (status) {
      case 'landed':
        return theme.colors.success;
      case 'delayed':
      case 'cancelled':
        return theme.colors.error;
      case 'boarding':
        return theme.colors.warning;
      default:
        return theme.colors.text;
    }
  };

  const getStatusDisplay = (status?: string): string => {
    if (!status) return 'Unknown';
    return status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ');
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.surface, borderColor: theme.colors.border }]}>
      {/* Time */}
      <View style={styles.timeColumn}>
        <Text style={[styles.timeText, { color: theme.colors.text }]}>
          {formatTime(flight.departureTime || flight.arrivalTime)}
        </Text>
      </View>

      {/* Flight Number & Airline */}
      <View style={styles.flightColumn}>
        {showAirline && flight.airlineIATA && (
          <View style={[styles.airlineBadge, { backgroundColor: theme.colors.primary }]}>
            <Text style={[styles.airlineText, { color: theme.colors.text }]}>
              {flight.airlineIATA}
            </Text>
          </View>
        )}
        <Text style={[styles.flightNumber, { color: theme.colors.text }]}>
          {flight.flightNumber}
        </Text>
      </View>

      {/* Route (From/To) */}
      <View style={styles.routeColumn}>
        <Text style={[styles.routeText, { color: theme.colors.text }]}>
          {flight.originIATA || flight.origin || 'N/A'}
        </Text>
        <Text style={[styles.routeArrow, { color: theme.colors.textSecondary }]}> → </Text>
        <Text style={[styles.routeText, { color: theme.colors.text }]}>
          {flight.destinationIATA || flight.destination || 'N/A'}
        </Text>
      </View>

      {/* Status */}
      {showStatus && (
        <View style={styles.statusColumn}>
          <Text style={[styles.statusText, { color: getStatusColor(flight.status) }]}>
            {getStatusDisplay(flight.status)}
          </Text>
        </View>
      )}

      {/* Altitude */}
      <View style={styles.dataColumn}>
        <Text style={[styles.dataLabel, { color: theme.colors.textSecondary }]}>ALT</Text>
        <Text style={[styles.dataValue, { color: theme.colors.text }]}>
          {flight.altitude ? `${Math.round(flight.altitude / 1000)}k ft` : 'N/A'}
        </Text>
      </View>

      {/* Speed */}
      <View style={styles.dataColumn}>
        <Text style={[styles.dataLabel, { color: theme.colors.textSecondary }]}>SPD</Text>
        <Text style={[styles.dataValue, { color: theme.colors.text }]}>
          {flight.speed ? `${flight.speed} kts` : 'N/A'}
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    paddingVertical: 16,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    alignItems: 'center',
  },
  timeColumn: {
    width: 80,
    paddingHorizontal: 8,
  },
  timeText: {
    fontSize: 18,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  flightColumn: {
    flexDirection: 'row',
    alignItems: 'center',
    width: 120,
    paddingHorizontal: 8,
  },
  airlineBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginRight: 8,
  },
  airlineText: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  flightNumber: {
    fontSize: 16,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  routeColumn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
  },
  routeText: {
    fontSize: 16,
    fontWeight: '600',
  },
  routeArrow: {
    fontSize: 14,
    marginHorizontal: 4,
  },
  statusColumn: {
    width: 120,
    paddingHorizontal: 8,
  },
  statusText: {
    fontSize: 14,
    fontWeight: 'bold',
    textTransform: 'uppercase',
  },
  dataColumn: {
    width: 90,
    paddingHorizontal: 8,
  },
  dataLabel: {
    fontSize: 10,
    marginBottom: 2,
  },
  dataValue: {
    fontSize: 14,
    fontWeight: '600',
    fontFamily: 'monospace',
  },
});
```

---

## File: src/components/FlightBoard.tsx

```typescript
import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Dimensions,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { Flight, FlightView, Theme, ColumnConfig } from '../types/Flight';
import { FlightHeader } from './FlightHeader';
import { FlightRow } from './FlightRow';

interface FlightBoardProps {
  flights: Flight[];
  view: FlightView;
  theme: Theme;
  onRefresh?: () => void;
  refreshing?: boolean;
  title?: string;
}

const defaultColumns: ColumnConfig[] = [
  { key: 'time', label: 'Time', width: 80, visible: true, sortable: true },
  { key: 'flightNumber', label: 'Flight', width: 120, visible: true, sortable: true },
  { key: 'origin', label: 'Route', visible: true, sortable: true },
  { key: 'status', label: 'Status', width: 120, visible: true, sortable: true },
  { key: 'altitude', label: 'Altitude', width: 90, visible: true, sortable: true },
  { key: 'speed', label: 'Speed', width: 90, visible: true, sortable: true },
];

/**
 * Main flight board component displaying a list of flights in airport monitor style
 */
export const FlightBoard: React.FC<FlightBoardProps> = ({
  flights,
  view,
  theme,
  onRefresh,
  refreshing = false,
  title,
}) => {
  const [sortedFlights, setSortedFlights] = useState<Flight[]>(flights);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update current time every minute
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

  // Sort flights when they change
  useEffect(() => {
    const sorted = [...flights].sort((a, b) => {
      // Sort by time (departure for departures, arrival for arrivals)
      const timeA = view === 'departures'
        ? new Date(a.departureTime || 0).getTime()
        : new Date(a.arrivalTime || 0).getTime();
      const timeB = view === 'departures'
        ? new Date(b.departureTime || 0).getTime()
        : new Date(b.arrivalTime || 0).getTime();
      
      return timeA - timeB;
    });
    setSortedFlights(sorted);
  }, [flights, view]);

  const formatDateTime = (date: Date): string => {
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }) + ' ' + date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    });
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      {/* Header with title and current time */}
      <View style={[styles.header, { backgroundColor: theme.colors.primary }]}>
        <View style={styles.headerLeft}>
          <Text style={[styles.title, { color: theme.colors.text }]}>
            {title || (view === 'arrivals' ? 'Arrivals' : 'Departures')}
          </Text>
          <Text style={[styles.flightCount, { color: theme.colors.text }]}>
            {sortedFlights.length} {sortedFlights.length === 1 ? 'flight' : 'flights'}
          </Text>
        </View>
        <View style={styles.headerRight}>
          <Text style={[styles.currentTime, { color: theme.colors.text }]}>
            {formatDateTime(currentTime)}
          </Text>
        </View>
      </View>

      {/* Column headers */}
      <FlightHeader columns={defaultColumns} theme={theme} />

      {/* Flight list */}
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          onRefresh ? (
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={theme.colors.primary}
              colors={[theme.colors.primary]}
            />
          ) : undefined
        }
      >
        {sortedFlights.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={[styles.emptyText, { color: theme.colors.textSecondary }]}>
              No flights to display
            </Text>
          </View>
        ) : (
          sortedFlights.map((flight, index) => (
            <FlightRow
              key={`${flight.flightNumber}-${index}`}
              flight={flight}
              theme={theme}
              showAirline={true}
              showStatus={true}
            />
          ))
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 20,
    paddingHorizontal: 16,
  },
  headerLeft: {
    flexDirection: 'column',
  },
  headerRight: {
    flexDirection: 'column',
    alignItems: 'flex-end',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  flightCount: {
    fontSize: 14,
    opacity: 0.9,
  },
  currentTime: {
    fontSize: 16,
    fontWeight: '600',
    fontFamily: 'monospace',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 18,
  },
});
```

---

## File: src/App.tsx

```typescript
import React, { useState, useEffect } from 'react';
import { SafeAreaView, StatusBar, StyleSheet, View, Text, TouchableOpacity } from 'react-native';
import { FlightBoard } from './components/FlightBoard';
import { Flight, FlightView } from './types/Flight';
import { mockFlightService } from './services/MockFlightDataService';
import { themes, ThemeName, getTheme } from './themes/themes';

/**
 * Main App component for the Airport-Style Flight Monitor UI
 */
export default function App() {
  const [flights, setFlights] = useState<Flight[]>([]);
  const [view, setView] = useState<FlightView>('arrivals');
  const [themeName, setThemeName] = useState<ThemeName>('airportPurple');
  const [refreshing, setRefreshing] = useState(false);

  const theme = getTheme(themeName);

  // Initialize mock flight service
  useEffect(() => {
    // Subscribe to flight updates
    const unsubscribe = mockFlightService.subscribe((updatedFlights) => {
      setFlights(updatedFlights);
      setRefreshing(false);
    });

    // Start the service
    mockFlightService.start(5000); // Update every 5 seconds

    // Cleanup on unmount
    return () => {
      unsubscribe();
      mockFlightService.stop();
    };
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    // In a real app, this would trigger an API call
    // For now, the mock service will update automatically
    setTimeout(() => setRefreshing(false), 1000);
  };

  const toggleView = () => {
    setView(view === 'arrivals' ? 'departures' : 'arrivals');
  };

  const cycleTheme = () => {
    const themeNames: ThemeName[] = ['airportPurple', 'airportBlue', 'airportGreen', 'dark', 'light'];
    const currentIndex = themeNames.indexOf(themeName);
    const nextIndex = (currentIndex + 1) % themeNames.length;
    setThemeName(themeNames[nextIndex]);
  };

  return (
    <>
      <StatusBar
        barStyle={theme.isDark ? 'light-content' : 'dark-content'}
        backgroundColor={theme.colors.primary}
      />
      <SafeAreaView style={[styles.container, { backgroundColor: theme.colors.background }]}>
        {/* Control buttons */}
        <View style={[styles.controls, { backgroundColor: theme.colors.surface }]}>
          <TouchableOpacity
            style={[styles.button, { backgroundColor: theme.colors.primary }]}
            onPress={toggleView}
          >
            <Text style={[styles.buttonText, { color: theme.colors.text }]}>
              Switch to {view === 'arrivals' ? 'Departures' : 'Arrivals'}
            </Text>
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.button, { backgroundColor: theme.colors.secondary }]}
            onPress={cycleTheme}
          >
            <Text style={[styles.buttonText, { color: theme.colors.text }]}>
              Theme: {theme.name}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Flight board */}
        <FlightBoard
          flights={flights}
          view={view}
          theme={theme}
          onRefresh={handleRefresh}
          refreshing={refreshing}
        />
      </SafeAreaView>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  controls: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 12,
    paddingHorizontal: 16,
    gap: 12,
  },
  button: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: {
    fontSize: 14,
    fontWeight: 'bold',
  },
});
```

---

## File: README.md

```markdown
# Plane Tracker Monitor UI

Airport-style flight monitor UI for displaying tracked aircraft in real-time. Built with React Native for cross-platform mobile and web support.

![Reference Airport Monitor](https://github.com/user-attachments/assets/95d428b5-e6a8-4115-87cb-34446b1100d9)

## Features

- ✈️ **Airport-style display** with customizable themes
- 🎨 **5 pre-built color themes** (Airport Purple, Blue, Green, Dark, Light)
- 📱 **Responsive design** for phones and tablets
- 🔄 **Real-time updates** via pub/sub architecture
- 🌓 **Dark and light modes**
- 📊 **Arrivals and Departures views**
- 🔍 **Flight details**: time, airline, route, status, altitude, speed
- 📡 **Ready for AWS SNS/SQS or IoT Core integration**

## Quick Start

### Prerequisites

- Node.js 14+
- npm or yarn

### Installation

\`\`\`bash
# Clone the repository
git clone https://github.com/jromie0924/plane-tracker-monitor-ui.git
cd plane-tracker-monitor-ui

# Install dependencies
npm install
\`\`\`

### Development

\`\`\`bash
# Start web development server (opens at localhost:3000)
npm start

# Build for production
npm run build
\`\`\`

### React Native Mobile

\`\`\`bash
# Run on iOS (requires Mac + Xcode)
npm run ios

# Run on Android (requires Android Studio)
npm run android
\`\`\`

## Architecture

### Components

- **FlightBoard**: Main container with flight list and controls
- **FlightRow**: Individual flight display component
- **FlightHeader**: Column headers

### Data Flow

```
MockFlightDataService (Pub/Sub)
          ↓
    App Component
          ↓
    FlightBoard
          ↓
    FlightRow (×N)
```

### Themes

5 customizable themes included:

1. **Airport Purple** (default) - Purple theme inspired by airport monitors
2. **Airport Blue** - Bright blue alternative
3. **Airport Green** - Green theme option
4. **Dark** - Dark mode for night viewing
5. **Light** - Light mode for daytime

## Integration with plane-tracker-rgb-pi

### Option 1: AWS Pub/Sub (Recommended)

The Python tracker publishes to AWS SNS/SQS, and the mobile app subscribes for real-time updates. Cost: ~$0/month under free tier.

### Option 2: REST API

Poll a REST endpoint from the tracker at regular intervals.

### Option 3: WebSocket

Real-time bidirectional communication for instant updates.

See [MONITOR_UI_IMPLEMENTATION.md](../plane-tracker-rgb-pi/MONITOR_UI_IMPLEMENTATION.md) for detailed integration guide.

## Flight Data Format

```json
{
  "flightNumber": "AA1234",
  "airline": "American Airlines",
  "airlineIATA": "AA",
  "origin": "Chicago O'Hare",
  "destination": "Los Angeles",
  "originIATA": "ORD",
  "destinationIATA": "LAX",
  "altitude": 35000,
  "speed": 450,
  "status": "in_flight",
  "departureTime": "2026-02-14T10:30:00Z",
  "arrivalTime": "2026-02-14T14:45:00Z"
}
```

## Customization

### Add a New Theme

Edit `src/themes/themes.ts`:

```typescript
export const MyTheme: Theme = {
  name: 'My Theme',
  isDark: true,
  colors: {
    primary: '#YOUR_COLOR',
    // ... other colors
  },
};
```

### Change Update Frequency

Edit `src/App.tsx`:

```typescript
mockFlightService.start(10000); // Update every 10 seconds
```

## Scripts

- `npm start` - Start webpack dev server
- `npm run build` - Build for production
- `npm run ios` - Run on iOS
- `npm run android` - Run on Android
- `npm run lint` - Run ESLint
- `npm run type-check` - TypeScript type checking

## Tech Stack

- React Native
- TypeScript
- React Native Web
- Webpack
- Babel

## License

MIT - See LICENSE file for details

## Related Projects

- [plane-tracker-rgb-pi](https://github.com/jromie0924/plane-tracker-rgb-pi) - Python ADSB tracker for RGB LED matrix

## Contributing

Contributions welcome! Please open an issue or pull request.
```

---

## Setup Instructions for New Repository

1. **Create the directory structure** as shown above
2. **Copy each file** into its corresponding location
3. **Install dependencies**:
   ```bash
   npm install
   ```
4. **Start the development server**:
   ```bash
   npm start
   ```
5. **Open browser** to http://localhost:3000

## Testing the Application

The app includes mock data that simulates real-time flight updates. You'll see:
- Flight list with 15 initial flights
- Automatic updates every 5 seconds
- Changes to altitude, speed, and status
- Occasional flights added/removed

Test all 5 themes by clicking the "Theme" button!

---

**End of Complete Source Code Package**
