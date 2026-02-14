# TypeScript Implementation Guide

## Overview

The airport-style flight monitor UI is **fully implemented in TypeScript** with strict type checking enabled. This provides:

- **Type safety** at compile time
- **IntelliSense** support in editors
- **Better refactoring** capabilities
- **Self-documenting** code with type definitions
- **Fewer runtime errors**

## TypeScript Configuration

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "esnext",
    "module": "commonjs",
    "lib": ["esnext"],
    "jsx": "react-native",
    "strict": true,              // ✅ Strict mode enabled
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

**Key settings:**
- `strict: true` - Enables all strict type checking options
- `jsx: "react-native"` - Proper JSX handling for React Native
- `isolatedModules: true` - Ensures each file can be transpiled independently

## Type Definitions

### Flight Interface (src/types/Flight.ts)

Comprehensive flight data model with 20+ typed fields:

```typescript
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
  altitude?: number;
  altitudeMeters?: number;
  
  // Speed and heading
  speed?: number;
  speedKmh?: number;
  heading?: number;
  verticalRate?: number;
  
  // Time information
  departureTime?: string;
  arrivalTime?: string;
  estimatedArrivalTime?: string;
  
  // Status with discriminated union
  status?: 'scheduled' | 'boarding' | 'departed' | 'in_flight' | 'landed' | 'cancelled' | 'delayed';
  
  // Additional data
  distance?: number;
  squawk?: string;
  isOnGround?: boolean;
}
```

**Benefits:**
- Optional fields use `?` for clarity
- String literal types for `status` prevent typos
- Number types ensure correct data types
- Clear documentation with comments

### Theme System (src/types/Flight.ts + src/themes/themes.ts)

Strongly-typed theme system with autocomplete:

```typescript
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

// Type-safe theme names with autocomplete
export type ThemeName = 'airportPurple' | 'airportBlue' | 'airportGreen' | 'dark' | 'light';

// Type-safe theme getter
export const getTheme = (name: ThemeName): Theme => {
  return themes[name] || AirportPurpleTheme;
};
```

**Benefits:**
- ThemeName type provides autocomplete in IDEs
- Cannot pass invalid theme names
- Theme structure is enforced across all themes
- Color properties are consistent

### Component Props (Type-safe React Components)

All components have strongly-typed props:

```typescript
// FlightBoard component props
interface FlightBoardProps {
  flights: Flight[];
  view: FlightView;
  theme: Theme;
  onRefresh?: () => void;
  refreshing?: boolean;
  title?: string;
}

export const FlightBoard: React.FC<FlightBoardProps> = ({
  flights,
  view,
  theme,
  onRefresh,
  refreshing = false,
  title,
}) => {
  // Component implementation
};
```

**Benefits:**
- Props are validated at compile time
- Default values are type-checked
- Optional props clearly marked with `?`
- Editor provides autocomplete for props

## TypeScript Features Used

### 1. Union Types

```typescript
export type FlightView = 'arrivals' | 'departures';
export type ThemeName = 'airportPurple' | 'airportBlue' | 'airportGreen' | 'dark' | 'light';

// Status can only be one of these values
status?: 'scheduled' | 'boarding' | 'departed' | 'in_flight' | 'landed' | 'cancelled' | 'delayed';
```

### 2. Generic Types

```typescript
// React.FC is a generic type for functional components
export const FlightRow: React.FC<FlightRowProps> = ({ flight, theme }) => {
  // ...
};

// Array.from with type inference
const flights: Flight[] = Array.from({ length: count }, (_, i) => generateMockFlight(i));
```

### 3. Type Guards

```typescript
const formatTime = (dateString?: string): string => {
  if (!dateString) return '--:--';  // Type guard
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
};
```

### 4. Optional Chaining

```typescript
// Safe property access
const timeA = view === 'departures'
  ? new Date(a.departureTime || 0).getTime()
  : new Date(a.arrivalTime || 0).getTime();

// Display with fallback
{flight.originIATA || flight.origin || 'N/A'}
```

### 5. Type Inference

TypeScript infers types automatically:

```typescript
// Type inferred as Flight[]
const [flights, setFlights] = useState<Flight[]>([]);

// Type inferred as 'arrivals' | 'departures'
const [view, setView] = useState<FlightView>('arrivals');

// Return type inferred from Theme
export const getTheme = (name: ThemeName) => {
  return themes[name] || AirportPurpleTheme;
};
```

### 6. Readonly Types

```typescript
// Immutable array of listeners
private listeners: ((flights: Flight[]) => void)[] = [];

// Return a copy, not the original
getFlights(): Flight[] {
  return [...this.flights];
}
```

### 7. Discriminated Unions

```typescript
// Status determines color
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
```

## Type Checking

### During Development

```bash
# Check types without emitting files
npm run type-check

# Or use tsc directly
npx tsc --noEmit
```

### Editor Integration

Most editors (VS Code, WebStorm, etc.) provide:
- **Real-time type checking** as you type
- **Autocomplete** for properties and methods
- **Go to definition** for types
- **Inline documentation** from JSDoc comments
- **Refactoring tools** that respect types

### Build-time Checking

Webpack with ts-loader checks types during build:

```javascript
// webpack.config.js
{
  test: /\.(ts|tsx)$/,
  exclude: /node_modules/,
  use: {
    loader: 'ts-loader',
  },
}
```

## Common TypeScript Patterns

### Pattern 1: Optional Props with Defaults

```typescript
interface FlightRowProps {
  flight: Flight;
  theme: Theme;
  showAirline?: boolean;
  showStatus?: boolean;
}

export const FlightRow: React.FC<FlightRowProps> = ({
  flight,
  theme,
  showAirline = true,    // Default value
  showStatus = true,      // Default value
}) => {
  // ...
};
```

### Pattern 2: State with Types

```typescript
const [flights, setFlights] = useState<Flight[]>([]);
const [view, setView] = useState<FlightView>('arrivals');
const [themeName, setThemeName] = useState<ThemeName>('airportPurple');
```

### Pattern 3: Callback Types

```typescript
// Subscription callback type
subscribe(listener: (flights: Flight[]) => void): () => void {
  this.listeners.push(listener);
  
  // Return unsubscribe function with same type
  return () => {
    this.listeners = this.listeners.filter(l => l !== listener);
  };
}
```

### Pattern 4: Type Assertions

```typescript
// When you know more than TypeScript
const container = document.getElementById('root') as HTMLElement;
```

### Pattern 5: Utility Types

```typescript
// Pick specific properties
type FlightSummary = Pick<Flight, 'flightNumber' | 'status' | 'altitude'>;

// Make all properties optional
type PartialFlight = Partial<Flight>;

// Make all properties required
type RequiredFlight = Required<Flight>;

// Extract keys
type FlightKeys = keyof Flight;
```

## Benefits of TypeScript in This Project

### 1. Compile-Time Safety

❌ **Without TypeScript:**
```javascript
// Typo in property name - runtime error
<FlightRow fligt={flight} theme={theme} />

// Wrong type - runtime error
const altitude = flight.altitude.toUpperCase();
```

✅ **With TypeScript:**
```typescript
// Caught at compile time
<FlightRow fligt={flight} theme={theme} />
//         ^^^^^ Error: Property 'fligt' does not exist

// Type error caught immediately
const altitude = flight.altitude.toUpperCase();
//                                ^^^^^^^^^^^ Error: Property 'toUpperCase' does not exist on type 'number'
```

### 2. Refactoring Support

Renaming properties or methods updates all references:

```typescript
// Rename 'altitude' to 'altitudeFeet' in Flight interface
// TypeScript finds ALL usages automatically
```

### 3. Self-Documenting Code

```typescript
// Function signature documents expected types
function formatAltitude(altitude: number | undefined, units: 'feet' | 'meters'): string {
  // Implementation
}
```

### 4. Better Tooling

- Autocomplete for all properties
- Inline documentation from types
- Navigate to type definitions
- Find all references
- Automatic import suggestions

### 5. Easier Collaboration

Team members can see:
- What data structures look like
- What props components accept
- What functions return
- Optional vs required fields

## Migration from JavaScript

If you're coming from JavaScript:

1. **Start with .tsx files** - React components with JSX
2. **Use .ts files** - Pure TypeScript without JSX
3. **Add types gradually** - Start with `any`, then refine
4. **Enable strict mode** - Once comfortable with basics
5. **Use type inference** - Let TypeScript figure out types when obvious

## Resources

- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)
- [TypeScript with React Native](https://reactnative.dev/docs/typescript)

## Conclusion

The entire airport-style flight monitor UI is built with TypeScript, providing:

- ✅ **Type safety** throughout the codebase
- ✅ **Better developer experience** with autocomplete
- ✅ **Fewer bugs** caught at compile time
- ✅ **Self-documenting** code with clear interfaces
- ✅ **Easier refactoring** with confidence

All 10 source files use TypeScript (.ts/.tsx extensions) with strict mode enabled for maximum type safety!
